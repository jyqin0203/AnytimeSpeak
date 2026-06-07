import logging
import os
import re
import asyncio
import base64
import hashlib
import hmac
import json
import ssl
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
from typing import Any

import httpx
import websockets
from dotenv import load_dotenv

from app.schemas import PronunciationAssessmentRequest, PronunciationAssessmentResponse


PRONUNCIATION_TIMEOUT_SECONDS = 15.0

logger = logging.getLogger("uvicorn.error")


class PronunciationProviderError(ValueError):
    pass


async def assess_pronunciation_with_fallback(
    request: PronunciationAssessmentRequest,
) -> PronunciationAssessmentResponse:
    config_reason = _config_fallback_reason(request.provider_mode)
    if config_reason:
        return _mock_assessment(request, config_reason)

    try:
        provider_mode = _provider_mode(request.provider_mode)
        response = (
            await _xfyun_assessment(request)
            if provider_mode == "xfyun"
            else _api_assessment(request)
        )
        _log_provider_state(provider_mode)
        return response
    except Exception as exc:
        fallback_reason = _fallback_reason(exc)
        return _mock_assessment(request, fallback_reason)


def _api_assessment(request: PronunciationAssessmentRequest) -> PronunciationAssessmentResponse:
    base_url = _api_base_url().rstrip("/")
    payload = {
        "model": _api_model(),
        "session_id": request.session_id,
        "scenario_id": request.scenario_id,
        "transcript": request.transcript or request.user_message or "",
        "reference_text": request.reference_text or request.user_message or request.transcript or "",
        "audio_url": request.audio_url,
        "audio_duration_ms": request.audio_duration_ms,
        "recognized_language": request.recognized_language,
    }

    response = httpx.post(
        base_url,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=PRONUNCIATION_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise PronunciationProviderError("Pronunciation API response must be an object.")
    return _response_from_api_data(data)


def _response_from_api_data(data: dict[str, Any]) -> PronunciationAssessmentResponse:
    try:
        overall = _score(data.get("overall_score", data.get("overallScore")))
        return PronunciationAssessmentResponse(
            provider=str(data.get("provider") or "pronunciation_api"),
            pronunciation_score=_score(data.get("pronunciation_score", data.get("pronunciationScore", overall))),
            fluency_score=_score(data.get("fluency_score", data.get("fluencyScore", overall))),
            accuracy_score=_score(data.get("accuracy_score", data.get("accuracyScore", overall))),
            completeness_score=_score(data.get("completeness_score", data.get("completenessScore", overall))),
            rhythm_score=_optional_score(data.get("rhythm_score", data.get("rhythmScore"))),
            overall_score=overall,
            feedback_zh=str(data.get("feedback_zh") or data.get("feedbackZh") or "发音测评完成。"),
            strengths=_string_list(data.get("strengths")),
            improvement_tips=_string_list(data.get("improvement_tips", data.get("improvementTips"))),
            word_tips=_string_list(data.get("word_tips", data.get("wordTips"))),
            is_fallback=False,
        )
    except Exception as exc:
        raise PronunciationProviderError("Pronunciation API response schema is invalid.") from exc


async def _xfyun_assessment(request: PronunciationAssessmentRequest) -> PronunciationAssessmentResponse:
    if not request.audio_base64:
        raise PronunciationProviderError("XFYUN pronunciation assessment requires audio_base64.")
    reference = (request.reference_text or request.user_message or request.transcript or "").strip()
    if not reference:
        raise PronunciationProviderError("XFYUN pronunciation assessment requires reference_text.")

    audio_bytes = base64.b64decode(request.audio_base64)
    if not audio_bytes:
        raise PronunciationProviderError("XFYUN audio payload is empty.")

    url = _xfyun_authorized_url()
    payloads = _xfyun_payloads(audio_bytes, reference)
    result_chunks: list[str] = []

    ssl_context = ssl.create_default_context()
    async with websockets.connect(url, ssl=ssl_context, open_timeout=PRONUNCIATION_TIMEOUT_SECONDS) as websocket:
        for payload in payloads:
            await websocket.send(json.dumps(payload, ensure_ascii=False))
            raw_response = await asyncio.wait_for(websocket.recv(), timeout=PRONUNCIATION_TIMEOUT_SECONDS)
            data = json.loads(raw_response)
            if int(data.get("code", 0)) != 0:
                raise PronunciationProviderError("XFYUN pronunciation API returned non-zero code.")
            result = data.get("data", {}).get("data")
            if result:
                result_chunks.append(str(result))
            if int(data.get("data", {}).get("status", 0)) == 2:
                break

    if not result_chunks:
        raise PronunciationProviderError("XFYUN pronunciation API returned no result.")

    xml_text = base64.b64decode("".join(result_chunks)).decode("utf-8", errors="ignore")
    return _response_from_xfyun_xml(xml_text)


def _xfyun_authorized_url() -> str:
    base_url = _xfyun_base_url()
    parsed = urlparse(base_url)
    host = parsed.netloc
    path = parsed.path or "/v2/open-ise"
    date = format_datetime(datetime.now(timezone.utc), usegmt=True)
    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature_sha = hmac.new(
        _xfyun_api_secret().encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization_origin = (
        f'api_key="{_xfyun_api_key()}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
    query = urlencode({"authorization": authorization, "date": date, "host": host}, quote_via=quote)
    return f"{base_url}?{query}"


def _xfyun_payloads(audio_bytes: bytes, reference: str) -> list[dict[str, Any]]:
    frame_size = 1280
    frames = [audio_bytes[i : i + frame_size] for i in range(0, len(audio_bytes), frame_size)] or [b""]
    payloads: list[dict[str, Any]] = []
    encoded_reference = base64.b64encode(f"[content]\n{reference}".encode("utf-8")).decode("ascii")
    for index, frame in enumerate(frames):
        status = 0 if index == 0 else 1
        payload: dict[str, Any] = {
            "data": {
                "status": status,
                "data": base64.b64encode(frame).decode("ascii"),
            }
        }
        if index == 0:
            payload["common"] = {"app_id": _xfyun_app_id()}
            payload["business"] = {
                "sub": "ise",
                "ent": _xfyun_language(),
                "category": _xfyun_category(),
                "cmd": "ssb",
                "auf": _xfyun_audio_format(),
                "aue": "raw",
                "text": encoded_reference,
                "tte": "utf-8",
                "rstcd": "utf8",
            }
        payloads.append(payload)
    payloads.append(
        {
            "data": {
                "status": 2,
                "data": "",
            }
        }
    )
    return payloads


def _response_from_xfyun_xml(xml_text: str) -> PronunciationAssessmentResponse:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise PronunciationProviderError("XFYUN pronunciation XML is invalid.") from exc

    nodes = list(root.iter())
    score_source = _first_node_with_attrs(nodes, ("total_score", "accuracy_score", "fluency_score")) or root
    overall = _score(_first_number(score_source, "total_score", "score", "overall_score", default=75))
    accuracy = _score(_first_number(score_source, "accuracy_score", "phone_score", default=overall))
    fluency = _score(_first_number(score_source, "fluency_score", "fluency", default=overall))
    completeness = _score(_first_number(score_source, "integrity_score", "completeness_score", default=overall))
    pronunciation = _score(_first_number(score_source, "phone_score", "accuracy_score", default=accuracy))
    word_tips = _xfyun_word_tips(nodes)
    tips = ["跟读推荐句，注意单词重音和连读节奏"]
    if word_tips:
        tips.insert(0, f"重点练习：{', '.join(word_tips[:3])}")

    return PronunciationAssessmentResponse(
        provider="xfyun_pronunciation",
        pronunciation_score=pronunciation,
        fluency_score=fluency,
        accuracy_score=accuracy,
        completeness_score=completeness,
        rhythm_score=fluency,
        overall_score=overall,
        feedback_zh="科大讯飞语音评测已完成。本轮分数来自真实录音与参考文本的对比。",
        strengths=["已完成真实录音发音测评"],
        improvement_tips=tips[:3],
        word_tips=word_tips[:3],
        is_fallback=False,
    )


def _first_node_with_attrs(nodes: list[ET.Element], attrs: tuple[str, ...]) -> ET.Element | None:
    for node in nodes:
        if any(attr in node.attrib for attr in attrs):
            return node
    return None


def _first_number(node: ET.Element, *attrs: str, default: int) -> float:
    for attr in attrs:
        raw = node.attrib.get(attr)
        if raw is None:
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return float(default)


def _xfyun_word_tips(nodes: list[ET.Element]) -> list[str]:
    tips: list[str] = []
    for node in nodes:
        if node.tag.lower().endswith("word"):
            content = node.attrib.get("content") or node.attrib.get("word")
            score = _first_number(node, "total_score", "phone_score", "accuracy_score", default=100)
            if content and score < 75:
                tips.append(content)
    return _dedupe(tips)


def _mock_assessment(
    request: PronunciationAssessmentRequest,
    fallback_reason: str,
) -> PronunciationAssessmentResponse:
    transcript = (request.transcript or request.user_message or "").strip()
    reference = (request.reference_text or request.user_message or transcript).strip()
    features = _extract_features(transcript, reference, request.audio_duration_ms)

    if not transcript or features["word_count"] < 2:
        pronunciation = 58 if transcript else 52
        fluency = 54 if transcript else 50
        accuracy = 58 if transcript else 50
        completeness = 55 if transcript else 50
        feedback = "没有检测到足够语音内容，本轮只能给出保守估计。下一轮可以完整说出一句英文后再测评。"
        strengths = ["已经尝试开启语音练习"] if transcript else []
        tips = ["请尽量说出完整句子", "可以先慢一点，保证每个关键词清楚"]
        word_tips = _reference_word_tips(reference)
    else:
        pronunciation = 82
        fluency = 82
        accuracy = 82
        completeness = 82
        tips: list[str] = []
        strengths: list[str] = []

        if features["english_ratio"] >= 0.75:
            strengths.append("英文表达占比较高，适合进行发音和流利度练习")
            pronunciation += 3
        else:
            fluency -= 12
            completeness -= 10
            tips.append("可以先中英文混合开口，但建议逐步替换成完整英文表达")

        if features["word_count"] >= 6:
            strengths.append("语音输入内容比较完整")
            completeness += 4
        elif features["word_count"] <= 3:
            completeness -= 12
            fluency -= 6
            tips.append("试着把回答扩展成包含主语、动作和细节的一整句")

        similarity = features["similarity"]
        if similarity < 0.42:
            accuracy -= 18
            tips.append("本轮表达和推荐英文差距较大，可以跟读推荐句一次")
        elif similarity < 0.68:
            accuracy -= 8
            tips.append("关键词基本相关，下一步可以靠近推荐英文的句型")
        else:
            accuracy += 5
            strengths.append("表达和目标句型比较接近")

        if features["has_repetition_or_pause"]:
            fluency -= 10
            tips.append("减少重复词和停顿标记，先在心里分成两小段再说")

        if features["incomplete_marker"]:
            completeness -= 12
            fluency -= 6
            tips.append("句尾可以补上宾语或时间信息，让意思更完整")

        words_per_second = features["words_per_second"]
        if words_per_second is not None:
            if words_per_second < 1.1:
                fluency -= 7
                tips.append("语速略慢，可以在熟悉句子后连贯说完")
            elif words_per_second > 3.8:
                pronunciation -= 5
                tips.append("语速偏快，注意关键词的清晰度")
            else:
                strengths.append("语速比较适合口语练习")

        pronunciation = _score(pronunciation)
        fluency = _score(fluency)
        accuracy = _score(accuracy)
        completeness = _score(completeness)
        feedback = _feedback_text(transcript, reference, features, accuracy, fluency, completeness)
        if not strengths:
            strengths = ["主要意思可以被理解"]
        if not tips:
            tips = ["保持这个节奏，下一轮可以更注意重读关键词"]
        word_tips = _word_tips(transcript, reference)

    rhythm = _score(round(fluency * 0.65 + pronunciation * 0.35))
    overall = _score(round(pronunciation * 0.30 + fluency * 0.25 + accuracy * 0.25 + completeness * 0.20))
    response = PronunciationAssessmentResponse(
        provider="heuristic_mock",
        pronunciation_score=pronunciation,
        fluency_score=fluency,
        accuracy_score=accuracy,
        completeness_score=completeness,
        rhythm_score=rhythm,
        overall_score=overall,
        feedback_zh=feedback,
        strengths=_dedupe(strengths)[:3],
        improvement_tips=_dedupe(tips)[:3],
        word_tips=_dedupe(word_tips)[:3],
        is_fallback=True,
    )
    _log_provider_state("heuristic_mock", fallback_reason)
    return response


def _extract_features(transcript: str, reference: str, duration_ms: int | None) -> dict[str, Any]:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", transcript)
    english_words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", transcript)
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[\u4e00-\u9fff]", transcript)
    normalized_transcript = _normalize_text(transcript)
    normalized_reference = _normalize_text(reference)
    similarity = (
        SequenceMatcher(None, normalized_transcript, normalized_reference).ratio()
        if normalized_transcript and normalized_reference
        else 0.0
    )
    lower_words = [word.lower() for word in english_words]
    repeated = any(a == b for a, b in zip(lower_words, lower_words[1:]))
    pause_marker = bool(re.search(r"\b(um+|uh+|er+|ah+|hmm+)\b|\.{2,}|,{2,}", transcript, re.IGNORECASE))
    incomplete_marker = bool(re.search(r"\b(and|but|because|so|to|for|with)\s*$", transcript.strip(), re.IGNORECASE))
    words_per_second = None
    if duration_ms and duration_ms > 0 and english_words:
        words_per_second = len(english_words) / (duration_ms / 1000)
    english_ratio = len(english_words) / max(1, len(tokens))

    return {
        "word_count": len(english_words),
        "chinese_count": len(chinese_chars),
        "english_ratio": english_ratio,
        "similarity": similarity,
        "has_repetition_or_pause": repeated or pause_marker,
        "incomplete_marker": incomplete_marker,
        "words_per_second": words_per_second,
    }


def _feedback_text(
    transcript: str,
    reference: str,
    features: dict[str, Any],
    accuracy: int,
    fluency: int,
    completeness: int,
) -> str:
    if features["english_ratio"] < 0.65:
        return "这轮能看出你在尝试表达意思，但中文或混合内容偏多。可以先开口，再逐步换成完整英文句子。"
    if accuracy < 70:
        return f"这句话整体可以听懂，但和推荐表达差距较大。可以跟读：{reference}"
    if fluency < 72:
        return "主要意思清楚，但流利度受停顿、重复或语速影响。建议先分成短语练习，再连起来说。"
    if completeness < 72:
        return "发音基础可用，但句子还不够完整。下一轮可以补上对象、原因或时间信息。"
    if "recently" in transcript.lower() and "been up to" in reference.lower():
        return "这句话整体可以听懂，但表达略不自然。询问近况时，英语里更常用现在完成时。"
    return "这轮表达比较完整，主要意思可以被理解。下一步可以注意关键词重读和更自然的句型。"


def _word_tips(transcript: str, reference: str) -> list[str]:
    ref_words = [w.lower() for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", reference)]
    said_words = {w.lower() for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", transcript)}
    missing = [w for w in ref_words if len(w) > 3 and w not in said_words]
    if missing:
        return missing[:2]
    return _reference_word_tips(reference)


def _reference_word_tips(reference: str) -> list[str]:
    phrases = re.findall(r"[A-Za-z]+(?:\s+[A-Za-z]+){0,2}", reference)
    return [phrase.strip() for phrase in phrases if len(phrase.strip()) > 3][:3]


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower()))


def _config_fallback_reason(requested_mode: str | None) -> str | None:
    _load_dotenv_files()
    provider_mode = _provider_mode(requested_mode)
    if provider_mode not in {"api", "xfyun"}:
        return "provider_mode_not_api"
    if provider_mode == "xfyun":
        if not _xfyun_app_id():
            return "missing_xfyun_app_id"
        if not _xfyun_api_key():
            return "missing_xfyun_api_key"
        if not _xfyun_api_secret():
            return "missing_xfyun_api_secret"
        return None
    if not _api_key():
        return "missing_api_key"
    if not _api_base_url():
        return "missing_base_url"
    return None


def _provider_mode(requested_mode: str | None) -> str:
    return (requested_mode or os.getenv("PRONUNCIATION_PROVIDER_MODE", "mock")).strip().lower()


def _load_dotenv_files() -> None:
    if os.getenv("ANYTIMESPEAK_SKIP_DOTENV", "").strip() == "1":
        return
    backend_dir = Path(__file__).resolve().parents[1]
    for path in (backend_dir.parent / ".env", backend_dir / ".env"):
        if path.exists():
            load_dotenv(path, override=False)


def _api_key() -> str:
    return os.getenv("PRONUNCIATION_API_KEY", "").strip()


def _api_base_url() -> str:
    return os.getenv("PRONUNCIATION_API_BASE_URL", "").strip()


def _api_model() -> str:
    return os.getenv("PRONUNCIATION_MODEL", "").strip() or "pronunciation-assessment"


def _xfyun_app_id() -> str:
    return os.getenv("XFYUN_APP_ID", "").strip()


def _xfyun_api_key() -> str:
    return os.getenv("XFYUN_API_KEY", "").strip()


def _xfyun_api_secret() -> str:
    return os.getenv("XFYUN_API_SECRET", "").strip()


def _xfyun_base_url() -> str:
    return os.getenv("XFYUN_ISE_BASE_URL", "").strip() or "wss://ise-api.xfyun.cn/v2/open-ise"


def _xfyun_language() -> str:
    return os.getenv("XFYUN_ISE_LANGUAGE", "").strip() or "en_vip"


def _xfyun_category() -> str:
    return os.getenv("XFYUN_ISE_CATEGORY", "").strip() or "read_sentence"


def _xfyun_audio_format() -> str:
    return os.getenv("XFYUN_ISE_AUDIO_FORMAT", "").strip() or "audio/L16;rate=16000"


def _fallback_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "pronunciation_api_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"pronunciation_api_http_{exc.response.status_code}"
    if isinstance(exc, PronunciationProviderError):
        message = str(exc)
        return "xfyun_pronunciation_failed" if "XFYUN" in message else "pronunciation_api_schema_invalid"
    if isinstance(exc, (websockets.WebSocketException, asyncio.TimeoutError, json.JSONDecodeError)):
        return "xfyun_pronunciation_failed"
    return "pronunciation_api_failed"


def _log_provider_state(provider: str, fallback_reason: str | None = None) -> None:
    log = logger.warning if fallback_reason else logger.info
    log(
        "pronunciation_provider: provider=%s provider_mode=%s api_key_present=%s fallback_reason=%s",
        provider,
        _provider_mode(None),
        bool(_api_key() or _xfyun_api_key()),
        fallback_reason or "none",
    )


def _score(value: Any) -> int:
    return max(0, min(100, int(round(float(value)))))


def _optional_score(value: Any) -> int | None:
    if value is None:
        return None
    return _score(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result
