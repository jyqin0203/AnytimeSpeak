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


LLM_TIMEOUT_SECONDS = 20.0
DEFAULT_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_LLM_MODEL = "qwen-plus"

logger = logging.getLogger(__name__)


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


def _log_llm_attempt(operation: str) -> None:
    logger.info("llm_provider: provider_mode=llm, attempting %s via LLM provider", operation)


def _log_fallback(operation: str, error: Exception) -> None:
    # Log only the operation and exception type — never the exception message or
    # request payload, since either could end up echoing configuration values.
    logger.warning(
        "llm_provider: %s via LLM provider failed (%s); falling back to mock provider",
        operation,
        type(error).__name__,
    )


def _log_fallback_reason(operation: str, reason: str) -> None:
    logger.warning(
        "llm_provider: %s fallback reason=%s provider_mode=%s api_key_present=%s base_url_present=%s model_present=%s",
        operation,
        reason,
        os.getenv("LLM_PROVIDER_MODE", "mock").strip().lower(),
        bool(_llm_api_key()),
        bool(_llm_base_url()),
        bool(_llm_model()),
    )


def create_chat_reply_with_fallback(request: ChatRequest) -> ChatResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_chat_reply(request, config_reason)

    _log_llm_attempt("chat reply")
    try:
        data = _json_from_llm(_request_chat_completion(_chat_prompt(request)))
        quick_feedback = _feedback_from_data(data.get("quick_feedback", {}))
        quick_feedback.provider = "llm"
        quick_feedback.fallback_reason = None
        return ChatResponse(
            session_id=request.session_id or "llm-session",
            scenario_id=request.scenario_id,
            reply=_chat_message_from_data(data.get("reply")),
            quick_feedback=quick_feedback,
            provider="llm",
        )
    except Exception as exc:
        _log_fallback("chat reply", exc)
        return _mock_chat_reply(request, _fallback_reason(exc))


def create_feedback_with_fallback(request: FeedbackRequest) -> FeedbackResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_feedback(request, config_reason)

    _log_llm_attempt("feedback")
    try:
        data = _json_from_llm(_request_chat_completion(_feedback_prompt(request)))
        feedback = _feedback_from_data(data)
        feedback.provider = "llm"
        feedback.fallback_reason = None
        return feedback
    except Exception as exc:
        _log_fallback("feedback", exc)
        return _mock_feedback(request, _fallback_reason(exc))


def create_summary_with_fallback(request: SummaryRequest) -> SummaryResponse:
    config_reason = _llm_config_fallback_reason()
    if config_reason:
        return _mock_summary(request, config_reason)

    _log_llm_attempt("session summary")
    try:
        data = _json_from_llm(_request_chat_completion(_summary_prompt(request)))
        scores = data.get("scores", {})
        return SummaryResponse(
            scenario_id=request.scenario_id,
            summary=str(data["summary"]),
            strengths=_string_list(data["strengths"]),
            repeated_issues=_string_list(data["repeated_issues"]),
            better_expressions=_string_list(data["better_expressions"]),
            scenario_completion=str(data["scenario_completion"]),
            next_practice_focus=str(data["next_practice_focus"]),
            code_switching_advice=_optional_string(data.get("code_switching_advice")),
            scores=ScoreBreakdown(
                grammar=int(scores["grammar"]),
                expression=int(scores["expression"]),
                fluency=int(scores["fluency"]),
                scenario_completion=int(scores.get("scenario_completion", scores.get("completion"))),
                overall=int(scores["overall"]),
            ),
            provider="llm",
        )
    except Exception as exc:
        _log_fallback("session summary", exc)
        return _mock_summary(request, _fallback_reason(exc))


def _mock_chat_reply(request: ChatRequest, reason: str) -> ChatResponse:
    response = mock_service.create_chat_reply(request)
    response.provider = "mock"
    response.fallback_reason = reason
    response.quick_feedback.provider = "mock"
    response.quick_feedback.fallback_reason = reason
    _log_fallback_reason("chat reply", reason)
    return response


def _mock_feedback(request: FeedbackRequest, reason: str) -> FeedbackResponse:
    response = mock_service.create_feedback(request)
    response.provider = "mock"
    response.fallback_reason = reason
    _log_fallback_reason("feedback", reason)
    return response


def _mock_summary(request: SummaryRequest, reason: str) -> SummaryResponse:
    response = mock_service.create_summary(request)
    response.provider = "mock"
    response.fallback_reason = reason
    _log_fallback_reason("session summary", reason)
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


def _request_chat_completion(messages: list[dict[str, str]]) -> str:
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
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload["choices"][0]["message"]["content"])


def _llm_api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()


def _llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL", "").strip() or DEFAULT_LLM_BASE_URL


def _llm_model() -> str:
    return os.getenv("LLM_MODEL", "").strip() or DEFAULT_LLM_MODEL


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
                    "above — never give generic, template-like follow-ups that could fit any "
                    "scenario, and vary your sentence patterns across turns so the conversation "
                    "feels alive rather than scripted. "
                    "Keep replies natural, brief (one to three sentences), and easy to read aloud "
                    "for spoken practice. "
                    "If the learner's message is unclear, briefly acknowledge what you did "
                    "understand and ask exactly one specific clarifying question. "
                    "If the learner drifts off-topic, respond naturally and briefly, then gently "
                    "steer the conversation back toward the scenario goal while staying in character. "
                    "If the learner mixes Chinese and English, infer their meaning and continue "
                    "naturally in your AI role — never break character to translate or lecture "
                    "about language. "
                    "Return JSON only with keys reply and quick_feedback. "
                    "reply must include role='assistant' and content. "
                    "quick_feedback must include what_you_said, user_intent, "
                    "recommended_english, issue, why, more_natural_option, "
                    "score, score_breakdown, and provider. "
                    "Keep quick_feedback brief and encouraging."
                ),
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario id: {request.scenario_id}\n"
                f"Previous conversation:\n{history}\n"
                f"Latest user message: {latest_user_message}\n"
                "Continue the role-play with one concise assistant reply and brief feedback."
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


def _json_from_llm(content: str) -> dict[str, Any]:
    candidates = [content, *_code_fence_contents(content)]
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(content[start : end + 1])

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate.strip())
        except json.JSONDecodeError as exc:
            last_error = exc
            continue

        if not isinstance(parsed, dict):
            raise LLMResponseParseError("LLM response must be a JSON object.")
        return parsed

    logger.warning("llm_provider: parse_failed response_length=%s", len(content))
    raise LLMResponseParseError("LLM response JSON parsing failed.") from last_error


def _code_fence_contents(content: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)]


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
    if isinstance(data, dict):
        return ChatMessage(
            role=data.get("role", "assistant"),
            content=str(data["content"]),
        )
    return ChatMessage(role="assistant", content=str(data))


def _feedback_from_data(data: Any) -> FeedbackResponse:
    if not isinstance(data, dict):
        raise ValueError("Feedback must be a JSON object.")
    if "what_you_said" in data:
        score = int(data["score"])
        return FeedbackResponse(
            what_you_said=str(data["what_you_said"]),
            user_intent=str(data["user_intent"]),
            recommended_english=str(data["recommended_english"]),
            issue=str(data["issue"]),
            why=str(data["why"]),
            more_natural_option=str(data["more_natural_option"]),
            score=score,
            score_breakdown=_score_breakdown_from_data(data.get("score_breakdown"), score),
            provider="llm",
            corrected_sentence=str(data["recommended_english"]),
            better_expression=str(data["more_natural_option"]),
            user_intent_zh=_optional_string(data.get("user_intent")),
            code_switching_tip=_optional_string(data.get("why")),
        )

    score = int(data["score"])
    return FeedbackResponse(
        what_you_said=str(data.get("what_you_said", "")),
        user_intent=_optional_string(data.get("user_intent_zh")) or "",
        recommended_english=str(data["corrected_sentence"]),
        issue=str(data["issue"]),
        why=_optional_string(data.get("code_switching_tip")) or str(data["issue"]),
        more_natural_option=str(data["better_expression"]),
        score=score,
        score_breakdown=_score_breakdown_from_data(data.get("score_breakdown"), score),
        provider="llm",
        corrected_sentence=str(data["corrected_sentence"]),
        better_expression=str(data["better_expression"]),
        user_intent_zh=_optional_string(data.get("user_intent_zh")),
        code_switching_tip=_optional_string(data.get("code_switching_tip")),
    )


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


def _clamp_breakdown_value(value: Any) -> int:
    return max(0, min(100, int(value)))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("Expected a list.")
    return [str(item) for item in value]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


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
