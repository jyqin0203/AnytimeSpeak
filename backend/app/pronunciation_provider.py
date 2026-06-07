import logging
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from app.schemas import PronunciationAssessmentRequest, PronunciationAssessmentResponse


PRONUNCIATION_TIMEOUT_SECONDS = 15.0

logger = logging.getLogger("uvicorn.error")


class PronunciationProviderError(ValueError):
    pass


def assess_pronunciation_with_fallback(
    request: PronunciationAssessmentRequest,
) -> PronunciationAssessmentResponse:
    config_reason = _config_fallback_reason(request.provider_mode)
    if config_reason:
        return _mock_assessment(request, config_reason)

    try:
        response = _api_assessment(request)
        _log_provider_state("api")
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
    provider_mode = (requested_mode or os.getenv("PRONUNCIATION_PROVIDER_MODE", "mock")).strip().lower()
    if provider_mode != "api":
        return "provider_mode_not_api"
    if not _api_key():
        return "missing_api_key"
    if not _api_base_url():
        return "missing_base_url"
    return None


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


def _fallback_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "pronunciation_api_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"pronunciation_api_http_{exc.response.status_code}"
    if isinstance(exc, PronunciationProviderError):
        return "pronunciation_api_schema_invalid"
    return "pronunciation_api_failed"


def _log_provider_state(provider: str, fallback_reason: str | None = None) -> None:
    log = logger.warning if fallback_reason else logger.info
    log(
        "pronunciation_provider: provider=%s provider_mode=%s api_key_present=%s fallback_reason=%s",
        provider,
        os.getenv("PRONUNCIATION_PROVIDER_MODE", "mock").strip().lower(),
        bool(_api_key()),
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
