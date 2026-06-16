import ast
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from app import mock_service
from app.scenario_catalog import get_scenario_prompt_config
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeedbackScoreBreakdown,
    FeedbackRequest,
    FeedbackResponse,
    Scenario,
    ScoreBreakdown,
    SummaryRequest,
    SummaryResponse,
)


LLM_TIMEOUT_SECONDS = 90.0
CHAT_TIMEOUT_SECONDS = 25.0
CHAT_REPLY_MAX_CHARS = 260
FEEDBACK_SHORT_MAX_CHARS = 90
FEEDBACK_MEDIUM_MAX_CHARS = 140
SUMMARY_TEXT_MAX_CHARS = 180
SUMMARY_ITEM_MAX_CHARS = 90

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


class LLMResponseParseError(ValueError):
    pass


def _dotenv_paths() -> list[Path]:
    backend_dir = Path(__file__).resolve().parents[1]
    project_root = backend_dir.parent
    return [project_root / ".env", backend_dir / ".env"]


def _load_dotenv_files() -> None:
    if os.getenv("ANYTIMESPEAK_SKIP_DOTENV", "").strip() == "1":
        return

    for path in _dotenv_paths():
        if path.exists():
            load_dotenv(path, override=False)


def _log_provider_state(
    operation: str,
    provider_result: str,
    fallback_reason: str | None = None,
) -> None:
    log = logger.warning if fallback_reason else logger.info
    log(
        "llm_provider: request_operation=%s provider_result=%s fallback_reason=%s "
        "provider_mode=%s api_key_present=%s base_url_present=%s model_present=%s",
        operation,
        provider_result,
        fallback_reason or "none",
        os.getenv("LLM_PROVIDER_MODE", "mock").strip().lower(),
        bool(_llm_api_key()),
        bool(_llm_base_url()),
        bool(_llm_model()),
    )


def _log_fallback(operation: str, error: Exception) -> None:
    # Log only the operation and exception type — never the exception message or
    # request payload, since either could end up echoing configuration values.
    logger.warning(
        "llm_provider: %s via LLM provider failed (%s); falling back to mock provider",
        operation,
        type(error).__name__,
    )


def create_chat_reply_with_fallback(request: ChatRequest) -> ChatResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_chat_reply(request, config_reason)

    try:
        raw_content = _request_chat_completion(_chat_prompt(request), timeout_seconds=CHAT_TIMEOUT_SECONDS)
        data = _chat_data_from_llm(raw_content)
        reply = _chat_message_from_data(_first_present(data, "reply", "message", "assistant_reply", "content", "text"))
        if _chat_reply_repeats_history(reply, _conversation_history(request)):
            raise ValueError("Chat reply repeated the previous assistant turn.")
        response = ChatResponse(
            session_id=request.session_id or "llm-session",
            scenario_id=request.scenario_id,
            reply=reply,
            provider="llm",
        )
        _log_provider_state("chat", "llm")
        return response
    except Exception as exc:
        _log_fallback("chat", exc)
        return _mock_chat_reply(request, _fallback_reason(exc))


def create_feedback_with_fallback(request: FeedbackRequest) -> FeedbackResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_feedback(request, config_reason)

    try:
        data = _json_from_llm(_request_chat_completion(_feedback_prompt(request)), "feedback")
        feedback = _feedback_from_data(data, request)
        feedback.provider = "llm"
        feedback.fallback_reason = None
        _log_provider_state("feedback", "llm")
        return feedback
    except Exception as exc:
        _log_fallback("feedback", exc)
        return _mock_feedback(request, _fallback_reason(exc))


def create_summary_with_fallback(request: SummaryRequest) -> SummaryResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_summary(request, config_reason)

    try:
        data = _json_from_llm(_request_chat_completion(_summary_prompt(request)), "summary")
        scores = data.get("scores") or data.get("score_breakdown") or {}
        response = SummaryResponse(
            scenario_id=request.scenario_id,
            summary=_clean_llm_text(data.get("summary") or "这次练习完成了主要对话目标。", SUMMARY_TEXT_MAX_CHARS),
            strengths=_string_list(data.get("strengths") or ["表达能被理解。"], limit=3, max_chars=SUMMARY_ITEM_MAX_CHARS),
            repeated_issues=_string_list(data.get("repeated_issues") or ["可以继续练习更自然的口语表达。"], limit=3, max_chars=SUMMARY_ITEM_MAX_CHARS),
            better_expressions=_string_list(data.get("better_expressions") or ["Could you tell me a little more?"], limit=3, max_chars=SUMMARY_ITEM_MAX_CHARS),
            scenario_completion=_clean_llm_text(data.get("scenario_completion") or "你完成了本轮场景的基本沟通。", SUMMARY_TEXT_MAX_CHARS),
            next_practice_focus=_clean_llm_text(data.get("next_practice_focus") or "下次可以补充更多具体细节。", SUMMARY_TEXT_MAX_CHARS),
            code_switching_advice=_optional_string(data.get("code_switching_advice"), SUMMARY_TEXT_MAX_CHARS),
            scores=ScoreBreakdown(
                grammar=_summary_score(data, scores, "grammar"),
                expression=_summary_score(data, scores, "expression", "naturalness"),
                fluency=_summary_score(data, scores, "fluency", "clarity"),
                scenario_completion=_summary_score(data, scores, "scenario_completion", "completion", "relevance"),
                overall=_summary_score(data, scores, "overall", "score"),
            ),
            provider="llm",
        )
        _log_provider_state("summary", "llm")
        return response
    except Exception as exc:
        _log_fallback("summary", exc)
        return _mock_summary(request, _fallback_reason(exc))


def _mock_chat_reply(request: ChatRequest, reason: str) -> ChatResponse:
    response = mock_service.create_chat_reply(request)
    response.provider = "mock"
    response.fallback_reason = reason
    _log_provider_state("chat", "mock", reason)
    return response


def _mock_feedback(request: FeedbackRequest, reason: str) -> FeedbackResponse:
    response = mock_service.create_feedback(request)
    response.provider = "mock"
    response.fallback_reason = reason
    _log_provider_state("feedback", "mock", reason)
    return response


def _mock_summary(request: SummaryRequest, reason: str) -> SummaryResponse:
    response = mock_service.create_summary(request)
    response.provider = "mock"
    response.fallback_reason = reason
    _log_provider_state("summary", "mock", reason)
    return response


def _llm_config_fallback_reason() -> str | None:
    _load_dotenv_files()
    provider_mode = os.getenv("LLM_PROVIDER_MODE", "mock").strip().lower()
    if provider_mode != "llm":
        return "provider_mode_not_llm"
    if not _llm_api_key():
        return "missing_api_key"
    if not _llm_base_url():
        return "missing_base_url"
    if not _llm_model():
        return "missing_model"
    return None


def _request_chat_completion(
    messages: list[dict[str, str]],
    timeout_seconds: float = LLM_TIMEOUT_SECONDS,
) -> str:
    base_url = _llm_base_url().rstrip("/")
    endpoint = (
        base_url
        if base_url.endswith("/chat/completions")
        else f"{base_url}/chat/completions"
    )

    response = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {_llm_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": _llm_model(),
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload["choices"][0]["message"]["content"])


def _llm_api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()


def _llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL", "").strip()


def _llm_model() -> str:
    return os.getenv("LLM_MODEL", "").strip()


def _chat_prompt(request: ChatRequest) -> list[dict[str, str]]:
    scenario = mock_service.resolve_scenario(request.session_id, request.scenario_id)
    history = _transcript(_conversation_history(request))
    latest_user_message = _latest_user_message(request)
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are the AI role in a spoken English roleplay practice session. "
                    "Ground every reply in the specific story, AI role, and conversation history "
                    "above. Never give generic, template-like follow-ups that could fit any "
                    "scenario, and vary your sentence patterns across turns so the conversation "
                    "feels alive rather than scripted. "
                    "Reply in 1-2 short natural English sentences under 45 words total. "
                    "Stay in role for the selected scenario. "
                    "Ask only one clear follow-up question. "
                    "Do not provide detailed grammar correction in the chat reply. "
                    "Keep the conversation natural and beginner-friendly. "
                    "Understand the learner's real meaning and emotion before replying. "
                    "If the learner expresses sadness, anxiety, tiredness, stress, fear, "
                    "frustration, nervousness, or Chinese emotion words such as 伤心, 难过, "
                    "累, 疲惫, 焦虑, 紧张, or 压力大, first respond with empathy, then ask one "
                    "gentle follow-up question. In those negative-emotion cases, do not use "
                    "positive stock phrases such as 'That sounds good', 'Great', 'Nice', "
                    "'Awesome', or 'Sounds fun'. "
                    "Use plain punctuation only: no em dashes, repeated punctuation, Markdown "
                    "bullets, numbered lists, slash-heavy wording, separator hyphens, or overly "
                    "formal coaching language. "
                    "If the learner's message is unclear, briefly acknowledge what you did "
                    "understand and ask one specific clarifying question. "
                    "If the learner drifts off-topic, respond naturally and briefly, then gently "
                    "steer the conversation back toward the scenario goal while staying in character. "
                    "If the learner mixes Chinese and English, infer their meaning and continue "
                    "naturally in your AI role. Never break character to translate or lecture "
                    "about language. "
                    "Scenario-specific grounding: in interview, ask about project, experience, "
                    "strengths, challenges, or results; in restaurant, respond as a server about "
                    "orders, recommendations, preferences, or confirmation; in meeting, ask about "
                    "progress, blockers, or next steps; in travel, focus on location, transport, "
                    "hotel, or help requests; in daily conversation, respond to the exact topic "
                    "the learner just mentioned. If the learner mentions lunch, food, homework, "
                    "class, go with me, want to come, or join me, respond to the plan or invitation "
                    "instead of asking a generic question about their day. "
                    "Return JSON only with key reply. reply must include role='assistant' "
                    "and content."
                ),
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario id: {request.scenario_id}\n"
                f"Previous conversation:\n{history}\n"
                f"Latest user message: {latest_user_message}\n"
                "Continue the role-play with one concise assistant reply."
            ),
        },
    ]


def _feedback_prompt(request: FeedbackRequest) -> list[dict[str, str]]:
    scenario = mock_service.resolve_scenario(request.session_id, request.scenario_id)
    history = _transcript(request.conversation_history)
    latest_user_message = request.latest_user_message or request.message or ""
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are an experienced, encouraging spoken-English coach reviewing exactly "
                    "ONE learner turn. Base your analysis strictly on the latest user message "
                    "below — never grade or reuse feedback from earlier turns; use the previous "
                    "conversation, the scenario, and the story only to understand the learner's "
                    "intent in this turn. "
                    "If the input mixes Chinese and English, first work out what the learner is "
                    "actually trying to say, then write recommended_english as a natural, fluent "
                    "English rewrite of THAT SAME message — never substitute an unrelated "
                    "template sentence. more_natural_option must also stay anchored in the "
                    "learner's actual words, offered as a slightly more natural or polished "
                    "alternative phrasing of the same idea. "
                    "Keep feedback compact for a small side card: user_intent, issue, and why "
                    "should each be one short sentence; recommended_english and "
                    "more_natural_option should each be one sentence. "
                    "For Chinese-English mixed input, never criticize the learner for mixing "
                    "languages, never say Chinese words are wrong or do not fit English habits, "
                    "and never make 'using Chinese words' the main issue. First acknowledge in "
                    "Chinese that the meaning is clear, then explain gently how to replace the "
                    "Chinese word with a natural English word, spoken collocation, or sentence "
                    "pattern while preserving the learner's original meaning and emotion. "
                    "For emotion words, focus on choices such as sad, upset, feeling down, "
                    "anxious, stressed, 'I'm feeling...', 'I've been feeling...', right now, "
                    "or lately. why must be 2-4 short Chinese sentences at most. "
                    "For daily plan or invitation turns, preserve the learner's real sequence "
                    "and explain in Chinese that English usually becomes clearer with a "
                    "time -> plan -> invitation order, such as after lunch, I’m planning to do "
                    "my homework, then Do you want to join me? "
                    "Because many learner turns come from speech recognition, do not treat "
                    "missing punctuation, capitalization, or sentence-final periods as the main "
                    "issue. Do not recommend a sentence only to add punctuation or capitalize "
                    "the first word unless the meaning is otherwise unclear. "
                    "Use plain punctuation only: no em dashes, repeated punctuation, Markdown, "
                    "bullet lists, separator hyphens, or long paragraphs. "
                    "Never reply with generic filler such as 'No major grammar issue'. Even when "
                    "the grammar is correct, comment on spoken naturalness, fit with the "
                    "scenario, or clarity, and suggest one concrete way to sound more like a "
                    "native speaker in this situation. "
                    "Keep issue, why, score, and score_breakdown internally consistent: a "
                    "problem you call out in issue must be reflected by a lower matching "
                    "score_breakdown component, and a turn you praise should score high. "
                    "Use 中文 explanations for issue and why so the learner can understand easily. "
                    "不要羞辱用户，不要说用户英语很差；像一位真人外教一样给出具体、可执行、鼓励式的反馈。 "
                    "Return JSON only with keys what_you_said, user_intent, recommended_english, "
                    "issue, why, more_natural_option, score, score_breakdown, and provider. "
                    "recommended_english and more_natural_option must be natural English. "
                    "issue and why should be concise Chinese explanations. "
                    "score_breakdown must contain integer fields grammar, naturalness, relevance, "
                    "and clarity from 0 to 100, and score must be the realistic overall "
                    "impression that follows from those four numbers — do not default to fixed "
                    "template values such as 80 or 88 every time. "
                    "Scoring guidance: Chinese-English mixed input does not have to lower "
                    "grammar, but naturalness and clarity should reasonably drop; a reply that "
                    "drifts from the scenario should lower relevance; Chinglish or unnatural "
                    "collocations should lower naturalness. "
                    "provider should be 'llm'."
                ),
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario id: {request.scenario_id}\n"
                f"Previous conversation for context only:\n{history}\n"
                f"Latest user message to evaluate — judge ONLY this message: {latest_user_message}"
            ),
        },
    ]


def _summary_prompt(request: SummaryRequest) -> list[dict[str, str]]:
    scenario = mock_service.resolve_scenario(request.session_id, request.scenario_id)
    history = _summary_history(request)
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are an English speaking coach creating a post-session summary. "
                    "Make the summary mostly in Chinese, but keep reusable expressions in English. "
                    "Assess performance using the scenario goal, the story the learner practiced, "
                    "and the scoring focus. "
                    "Keep the result compact: summary should be one short sentence; strengths, "
                    "repeated_issues, and better_expressions should contain at most three short "
                    "items each; scenario_completion and next_practice_focus should each be one "
                    "short sentence. "
                    "Use plain punctuation only: no em dashes, repeated punctuation, Markdown, "
                    "bullet markers inside strings, separator hyphens, or long paragraphs. "
                    "If the learner used Chinese-English mixed input multiple times, include a "
                    "practical 中英转换建议 in code_switching_advice. "
                    "Return JSON only with keys summary, strengths, repeated_issues, "
                    "better_expressions, scenario_completion, next_practice_focus, "
                    "code_switching_advice, scores, and provider. "
                    "scores must include grammar, expression, fluency, scenario_completion, "
                    "and overall from 0 to 100. provider should be 'llm'."
                ),
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario id: {request.scenario_id}\n"
                f"Conversation:\n{_transcript(history)}\n"
                "Create a concise post-session practice summary."
            ),
        },
    ]


def _json_from_llm(content: str, operation: str) -> dict[str, Any]:
    candidates = [content, *_code_fence_contents(content), *_json_value_candidates(content)]
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(content[start : end + 1])

    last_error: Exception | None = None
    seen: set[str] = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = _parse_json_like(candidate)
        except (json.JSONDecodeError, SyntaxError, ValueError) as exc:
            last_error = exc
            continue

        parsed_object = _first_json_object(parsed)
        if parsed_object is not None:
            return parsed_object
        last_error = LLMResponseParseError("LLM response must contain a JSON object.")

    logger.warning(
        "llm_provider: parse_failed operation=%s response_length=%s",
        operation,
        len(content),
    )
    raise LLMResponseParseError("LLM response JSON parsing failed.") from last_error


def _chat_data_from_llm(content: str) -> dict[str, Any]:
    try:
        return _json_from_llm(content, "chat")
    except LLMResponseParseError:
        cleaned = _clean_llm_text(content, CHAT_REPLY_MAX_CHARS)
        if not cleaned:
            raise
        logger.warning(
            "llm_provider: chat_plain_text_response response_length=%s",
            len(content),
        )
        return {"reply": {"role": "assistant", "content": cleaned}}


def _code_fence_contents(content: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)]


def _json_value_candidates(content: str) -> list[str]:
    candidates: list[str] = []
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "{[":
            continue
        try:
            parsed, end = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if _first_json_object(parsed) is not None:
            candidates.append(content[index : index + end])
    return candidates


def _parse_json_like(candidate: str) -> Any:
    last_error: Exception | None = None
    for variant in _json_candidate_variants(candidate):
        try:
            return json.loads(variant)
        except json.JSONDecodeError as exc:
            last_error = exc

        try:
            return ast.literal_eval(variant)
        except (SyntaxError, ValueError) as exc:
            last_error = exc

    raise json.JSONDecodeError("Unable to parse JSON-like LLM response.", candidate, 0) from last_error


def _json_candidate_variants(candidate: str) -> list[str]:
    normalized = candidate.strip()
    smart_quotes = str.maketrans(
        {
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
        }
    )
    normalized = normalized.translate(smart_quotes)
    without_trailing_commas = re.sub(r",\s*([}\]])", r"\1", normalized)
    quoted_keys = re.sub(
        r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
        r'\1"\2":',
        without_trailing_commas,
    )

    variants: list[str] = []
    for value in (candidate.strip(), normalized, without_trailing_commas, quoted_keys):
        if value and value not in variants:
            variants.append(value)
    return variants


def _first_json_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return None


def _fallback_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "llm_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"llm_http_{exc.response.status_code}"
    if isinstance(exc, LLMResponseParseError):
        return "json_parse_failed"
    if isinstance(exc, (KeyError, TypeError, ValueError)):
        return "schema_validation_failed"
    return "llm_request_failed"


def _chat_message_from_data(data: Any) -> ChatMessage:
    if data is None:
        raise ValueError("Chat reply is required.")
    if isinstance(data, dict):
        content = _first_optional(data, "content", "text", "message", "reply")
        if content is None:
            raise ValueError("Chat reply content is required.")
        return ChatMessage(
            role="assistant",
            content=_clean_llm_text(content, CHAT_REPLY_MAX_CHARS),
        )
    return ChatMessage(role="assistant", content=_clean_llm_text(data, CHAT_REPLY_MAX_CHARS))


def _feedback_from_data(data: Any, request: FeedbackRequest | None = None) -> FeedbackResponse:
    if not isinstance(data, dict):
        raise ValueError("Feedback must be a JSON object.")
    score = _score_from_data(data)
    latest_user_message = ""
    if request is not None:
        latest_user_message = request.latest_user_message or request.message or ""
    recommended_english = _clean_llm_text(
        _first_optional(
            data,
            "recommended_english",
            "recommended_expression",
            "corrected_sentence",
            "correction",
            "suggested_sentence",
        )
        or latest_user_message
        or "I see. Can you tell me a little more?",
        FEEDBACK_MEDIUM_MAX_CHARS,
    )
    more_natural_option = _clean_llm_text(
        _first_optional(
            data,
            "more_natural_option",
            "better_version",
            "better_expression",
            "natural_expression",
            "more_natural",
        )
        or recommended_english,
        FEEDBACK_MEDIUM_MAX_CHARS,
    )
    issue = _clean_llm_text(
        _first_optional(data, "issue", "main_issue", "problem", "focus")
        or "你的意思能理解，可以把句子整理得更自然、更清楚。",
        FEEDBACK_SHORT_MAX_CHARS,
    )
    why = _clean_llm_text(
        _first_optional(
            data,
            "why",
            "explanation",
            "reason",
            "why_it_is_more_natural",
            "code_switching_tip",
        )
        or "你的意思表达清楚了。换成更常用的英文词汇、语序或搭配后，听起来会更像自然口语。",
        FEEDBACK_MEDIUM_MAX_CHARS,
    )
    user_intent = _optional_string(
        _first_optional(data, "user_intent", "user_intent_zh", "intent", "meaning"),
        FEEDBACK_SHORT_MAX_CHARS,
    ) or ""
    response = FeedbackResponse(
        what_you_said=str(_first_optional(data, "what_you_said", "original_text", "user_message", "latest_user_message") or latest_user_message),
        user_intent=user_intent,
        recommended_english=recommended_english,
        issue=issue,
        why=why,
        more_natural_option=more_natural_option,
        score=score,
        score_breakdown=_score_breakdown_from_data(data.get("score_breakdown"), score),
        provider="llm",
        corrected_sentence=recommended_english,
        better_expression=more_natural_option,
        user_intent_zh=user_intent,
        code_switching_tip=why,
    )
    return _avoid_punctuation_only_feedback(response)


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    value = _first_optional(data, *keys)
    if value is not None:
        return value
    raise ValueError(f"Missing required field. Expected one of: {', '.join(keys)}")


def _first_optional(data: dict[str, Any], *keys: str) -> Any | None:
    for key in keys:
        value = data.get(key)
        if value is not None:
            if isinstance(value, str) and not value.strip():
                continue
            return value
    return None


def _score_from_data(data: dict[str, Any]) -> int:
    if data.get("score") is not None:
        return _clamp_breakdown_value(data["score"])
    breakdown = data.get("score_breakdown")
    if isinstance(breakdown, dict) and breakdown:
        values = [_clamp_breakdown_value(value) for value in breakdown.values()]
        return round(sum(values) / len(values))
    return 82


def _avoid_punctuation_only_feedback(response: FeedbackResponse) -> FeedbackResponse:
    if not _is_punctuation_only_change(response.what_you_said, response.recommended_english):
        return response
    if not _mentions_punctuation_or_capitalization(response.issue, response.why):
        return response

    original = _clean_llm_text(response.what_you_said, FEEDBACK_MEDIUM_MAX_CHARS)
    response.recommended_english = original
    response.corrected_sentence = original
    response.more_natural_option = original
    response.better_expression = original
    response.issue = "这句话的意思已经清楚了，语音输入里的大小写或句号不用作为主要问题。"
    response.why = "口语练习更应该关注表达是否自然、场景是否贴合，而不是只纠正识别文本里的标点。"
    response.code_switching_tip = response.why
    return response


def _is_punctuation_only_change(original: str, recommended: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    return bool(original.strip()) and normalize(original) == normalize(recommended)


def _mentions_punctuation_or_capitalization(*texts: str) -> bool:
    combined = " ".join(texts).lower()
    markers = (
        "punctuation",
        "capitalize",
        "capitalization",
        "period",
        "comma",
        "标点",
        "句号",
        "逗号",
        "大小写",
        "首字母",
    )
    return any(marker in combined for marker in markers)


def _score_breakdown_from_data(breakdown: Any, fallback_score: int) -> FeedbackScoreBreakdown:
    """Build a FeedbackScoreBreakdown from LLM output.

    Accepts the current grammar/naturalness/relevance/clarity keys, but also
    tolerates older or slightly different key names so a model that has not
    perfectly absorbed the new prompt still produces a usable breakdown.
    """
    source = breakdown if isinstance(breakdown, dict) else {}

    def pick(*keys: str) -> int:
        for key in keys:
            if key in source:
                return _clamp_breakdown_value(source[key])
        return _clamp_breakdown_value(fallback_score)

    return FeedbackScoreBreakdown(
        grammar=pick("grammar"),
        naturalness=pick("naturalness", "expression", "fluency"),
        relevance=pick("relevance", "scenario_fit", "scenario_completion"),
        clarity=pick("clarity", "fluency", "expression"),
    )


def _summary_score(data: dict[str, Any], scores: Any, *keys: str) -> int:
    sources = [scores if isinstance(scores, dict) else {}, data]
    for source in sources:
        for key in keys:
            if key in source:
                return _clamp_breakdown_value(source[key])
    return 82


def _clamp_breakdown_value(value: Any) -> int:
    if isinstance(value, str):
        text = value.strip()
        ratio_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", text)
        if ratio_match:
            numerator = float(ratio_match.group(1))
            denominator = float(ratio_match.group(2))
            if denominator:
                return max(0, min(100, round((numerator / denominator) * 100)))
        number_match = re.search(r"-?\d+(?:\.\d+)?", text)
        if number_match:
            value = number_match.group(0)
    return max(0, min(100, round(float(value))))


def _string_list(value: Any, *, limit: int | None = None, max_chars: int | None = None) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [item.strip(" -\t") for item in re.split(r"[\n;；]+", value) if item.strip(" -\t")]
    else:
        items = [value]
    items = items[:limit] if limit is not None else items
    return [_clean_llm_text(item, max_chars) for item in items]


def _optional_string(value: Any, max_chars: int | None = None) -> str | None:
    if value is None:
        return None
    return _clean_llm_text(value, max_chars)


def _clean_llm_text(value: Any, max_chars: int | None = None) -> str:
    text = str(value)
    text = re.sub(r"\s*[\u2014\u2015]\s*", ", ", text)
    text = re.sub(r"\s+\u2013\s+", ", ", text)
    text = re.sub(r"\s+-\s+", ", ", text)
    text = re.sub(r"([!?.,;:])\1+", r"\1", text)
    text = re.sub(r"\s+([!?.,;:])", r"\1", text)
    text = re.sub(r"[ \t\r\n]+", " ", text).strip()
    if max_chars is not None and len(text) > max_chars:
        text = _truncate_text(text, max_chars)
    return text


def _truncate_text(text: str, max_chars: int) -> str:
    clipped = text[:max_chars].rstrip()
    sentence_end = max(
        clipped.rfind("."),
        clipped.rfind("!"),
        clipped.rfind("?"),
        clipped.rfind("。"),
        clipped.rfind("！"),
        clipped.rfind("？"),
    )
    if sentence_end >= max_chars * 0.55:
        return clipped[: sentence_end + 1].strip()
    return clipped.rstrip(" ,;:，；：") + "..."


def _transcript(messages: list[ChatMessage]) -> str:
    if not messages:
        return "(no prior messages)"
    return "\n".join(f"{message.role}: {message.content}" for message in messages)


def _conversation_history(request: ChatRequest) -> list[ChatMessage]:
    return request.conversation_history or request.messages


def _summary_history(request: SummaryRequest) -> list[ChatMessage]:
    return request.conversation_history or request.messages


def _latest_user_message(request: ChatRequest) -> str:
    if request.latest_user_message:
        return request.latest_user_message
    for message in reversed(_conversation_history(request)):
        if message.role == "user":
            return message.content
    return ""


def _chat_reply_repeats_history(reply: ChatMessage, history: list[ChatMessage]) -> bool:
    for message in reversed(history):
        if message.role == "assistant":
            return _normalize_text(reply.content) == _normalize_text(message.content)
    return False


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _scenario_context(scenario: Scenario, extra_instructions: str) -> str:
    scoring_focus = get_scenario_prompt_config(scenario.scenario_id).scoring_focus
    return (
        "You are an English speaking practice partner for AnytimeSpeak.\n"
        f"Scenario: {scenario.title} / {scenario.title_zh}\n"
        f"Canonical scenario id: {scenario.scenario_id}\n"
        f"Story the learner sees (Chinese): {scenario.story_intro_zh}\n"
        f"Story the learner sees (English): {scenario.story_intro_en}\n"
        f"Opening line already shown to the learner: {scenario.opening_message}\n"
        f"AI role: {scenario.ai_role}\n"
        f"User role: {scenario.user_role}\n"
        f"Practice goal: {scenario.goal}\n"
        f"Suitable difficulty: {scenario.level}\n"
        f"Conversation style: {scenario.conversation_style}\n"
        f"Feedback focus: {_bullets(scenario.feedback_focus)}\n"
        f"Useful expressions: {_bullets(scenario.useful_expressions)}\n"
        f"Scoring focus: {_bullets(scoring_focus)}\n"
        "Code-switching policy: Chinese-English mixed input is allowed. "
        "Treat it as a low-pressure speaking bridge, infer the learner's intent, "
        "and guide them toward natural English.\n"
        f"Instructions: {extra_instructions}"
    )


def _bullets(items: list[str]) -> str:
    return "; ".join(items)
