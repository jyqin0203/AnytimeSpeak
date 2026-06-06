import json
import os
from typing import Any

import httpx

from app import mock_service
from app.scenario_catalog import ScenarioPromptConfig, get_scenario_prompt_config
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeedbackScoreBreakdown,
    FeedbackRequest,
    FeedbackResponse,
    ScoreBreakdown,
    SummaryRequest,
    SummaryResponse,
)


LLM_TIMEOUT_SECONDS = 20.0
DEFAULT_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_LLM_MODEL = "qwen-plus"


def create_chat_reply_with_fallback(request: ChatRequest) -> ChatResponse:
    if not _should_use_llm():
        return mock_service.create_chat_reply(request)

    try:
        data = _json_from_llm(_request_chat_completion(_chat_prompt(request)))
        return ChatResponse(
            session_id=request.session_id or "llm-session",
            scenario_id=request.scenario_id,
            reply=_chat_message_from_data(data.get("reply")),
            quick_feedback=_feedback_from_data(data.get("quick_feedback", {})),
        )
    except Exception:
        return mock_service.create_chat_reply(request)


def create_feedback_with_fallback(request: FeedbackRequest) -> FeedbackResponse:
    if not _should_use_llm():
        return mock_service.create_feedback(request)

    try:
        data = _json_from_llm(_request_chat_completion(_feedback_prompt(request)))
        return _feedback_from_data(data)
    except Exception:
        return mock_service.create_feedback(request)


def create_summary_with_fallback(request: SummaryRequest) -> SummaryResponse:
    if not _should_use_llm():
        return mock_service.create_summary(request)

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
        )
    except Exception:
        return mock_service.create_summary(request)


def _should_use_llm() -> bool:
    if os.getenv("LLM_PROVIDER_MODE", "mock").strip().lower() != "llm":
        return False

    return bool(_llm_api_key())


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
    return os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()


def _llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL", "").strip() or DEFAULT_LLM_BASE_URL


def _llm_model() -> str:
    return os.getenv("LLM_MODEL", "").strip() or DEFAULT_LLM_MODEL


def _chat_prompt(request: ChatRequest) -> list[dict[str, str]]:
    scenario = get_scenario_prompt_config(request.scenario_id)
    history = _transcript(_conversation_history(request))
    latest_user_message = _latest_user_message(request)
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are the AI role in a spoken English practice conversation. "
                    "Stay in the assigned AI role during reply.content. "
                    "Use mostly natural spoken English suitable for the scenario. "
                    "Ask one clear follow-up question at a time. "
                    "If the learner uses Chinese or Chinese-English mixed input, "
                    "understand the intent and continue the conversation naturally; "
                    "do not stop the role play or criticize the learner for code-switching. "
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
    scenario = get_scenario_prompt_config(request.scenario_id)
    history = _transcript(request.conversation_history)
    latest_user_message = request.latest_user_message or request.message or ""
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are an encouraging English speaking coach. "
                    "Support English, Chinese, and Chinese-English mixed learner input. "
                    "If the input contains Chinese, first infer the learner's intended meaning, "
                    "then provide a natural English sentence. "
                    "Only evaluate the latest user message. Use the previous conversation only "
                    "to understand context; never grade or reuse feedback from older turns. "
                    "Use 中文 explanations so the learner can understand easily. "
                    "不要羞辱用户，不要说用户英语很差；用鼓励式反馈。 "
                    "Return JSON only with keys what_you_said, user_intent, recommended_english, "
                    "issue, why, more_natural_option, score, score_breakdown, and provider. "
                    "recommended_english and more_natural_option must be natural English. "
                    "issue and why should be concise Chinese explanations. "
                    "score_breakdown must include grammar, expression, fluency, and scenario_fit from 0 to 100. "
                    "provider should be 'llm'."
                ),
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario id: {request.scenario_id}\n"
                f"Previous conversation for context only:\n{history}\n"
                f"Latest user message to evaluate: {latest_user_message}"
            ),
        },
    ]


def _summary_prompt(request: SummaryRequest) -> list[dict[str, str]]:
    scenario = get_scenario_prompt_config(request.scenario_id)
    history = _summary_history(request)
    return [
        {
            "role": "system",
            "content": _scenario_context(
                scenario,
                extra_instructions=(
                    "You are an English speaking coach creating a post-session summary. "
                    "Make the summary mostly in Chinese, but keep reusable expressions in English. "
                    "Assess performance using the scenario goal and scoring focus. "
                    "If the learner used Chinese-English mixed input multiple times, include a practical "
                    "中英转换建议 in code_switching_advice. "
                    "Return JSON only with keys summary, strengths, repeated_issues, "
                    "better_expressions, scenario_completion, next_practice_focus, "
                    "code_switching_advice, and scores. "
                    "scores must include grammar, expression, fluency, scenario_completion, "
                    "and overall from 0 to 100."
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
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(content[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object.")
    return parsed


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
        breakdown = data.get("score_breakdown", {})
        return FeedbackResponse(
            what_you_said=str(data["what_you_said"]),
            user_intent=str(data["user_intent"]),
            recommended_english=str(data["recommended_english"]),
            issue=str(data["issue"]),
            why=str(data["why"]),
            more_natural_option=str(data["more_natural_option"]),
            score=int(data["score"]),
            score_breakdown=FeedbackScoreBreakdown(
                grammar=int(breakdown["grammar"]),
                expression=int(breakdown["expression"]),
                fluency=int(breakdown["fluency"]),
                scenario_fit=int(breakdown["scenario_fit"]),
            ),
            provider=str(data.get("provider", "llm")),
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
        score_breakdown=FeedbackScoreBreakdown(
            grammar=max(0, min(100, score - 2)),
            expression=score,
            fluency=max(0, min(100, score + 2)),
            scenario_fit=max(0, min(100, score + 4)),
        ),
        provider=str(data.get("provider", "llm")),
        corrected_sentence=str(data["corrected_sentence"]),
        better_expression=str(data["better_expression"]),
        user_intent_zh=_optional_string(data.get("user_intent_zh")),
        code_switching_tip=_optional_string(data.get("code_switching_tip")),
    )


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


def _scenario_context(scenario: ScenarioPromptConfig, extra_instructions: str) -> str:
    return (
        "You are an English speaking practice partner for AnytimeSpeak.\n"
        f"Scenario: {scenario.title_en} / {scenario.title_zh}\n"
        f"Canonical scenario id: {scenario.scenario_id}\n"
        f"Scenario story: {scenario.story_intro}\n"
        f"AI role: {scenario.ai_role}\n"
        f"User role: {scenario.user_role}\n"
        f"Practice goal: {scenario.goal}\n"
        f"Suitable difficulty: {scenario.level}\n"
        f"Conversation style: {scenario.conversation_style}\n"
        f"Feedback focus: {_bullets(scenario.feedback_focus)}\n"
        f"Useful expressions: {_bullets(scenario.useful_expressions)}\n"
        f"Scoring focus: {_bullets(scenario.scoring_focus)}\n"
        "Code-switching policy: Chinese-English mixed input is allowed. "
        "Treat it as a low-pressure speaking bridge, infer the learner's intent, "
        "and guide them toward natural English.\n"
        f"Instructions: {extra_instructions}"
    )


def _bullets(items: list[str]) -> str:
    return "; ".join(items)
