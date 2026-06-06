import json
import os
from typing import Any

import httpx

from app import mock_service
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    ScoreBreakdown,
    SummaryRequest,
    SummaryResponse,
)


LLM_TIMEOUT_SECONDS = 20.0


def create_chat_reply_with_fallback(request: ChatRequest) -> ChatResponse:
    if not _should_use_llm():
        return mock_service.create_chat_reply(request)

    try:
        data = _json_from_llm(_request_chat_completion(_chat_prompt(request)))
        return ChatResponse(
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
            scores=ScoreBreakdown(
                grammar=int(scores["grammar"]),
                expression=int(scores["expression"]),
                fluency=int(scores["fluency"]),
                scenario_completion=int(scores["scenario_completion"]),
                overall=int(scores["overall"]),
            ),
        )
    except Exception:
        return mock_service.create_summary(request)


def _should_use_llm() -> bool:
    if os.getenv("LLM_PROVIDER_MODE", "mock").strip().lower() != "llm":
        return False

    return all(
        os.getenv(name, "").strip()
        for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
    )


def _request_chat_completion(messages: list[dict[str, str]]) -> str:
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    endpoint = (
        base_url
        if base_url.endswith("/chat/completions")
        else f"{base_url}/chat/completions"
    )

    response = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {os.environ['LLM_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.environ["LLM_MODEL"],
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload["choices"][0]["message"]["content"])


def _chat_prompt(request: ChatRequest) -> list[dict[str, str]]:
    transcript = _transcript(request.messages)
    return [
        {
            "role": "system",
            "content": (
                "You are an English speaking practice role-play assistant. "
                "Return JSON only with keys reply and quick_feedback. "
                "reply must include role='assistant' and content. "
                "quick_feedback must include corrected_sentence, issue, "
                "better_expression, and score from 0 to 100."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario: {request.scenario_id}\n"
                f"Conversation:\n{transcript}\n"
                "Continue the role-play with one concise assistant reply and brief feedback."
            ),
        },
    ]


def _feedback_prompt(request: FeedbackRequest) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an English speaking coach. Return JSON only with keys "
                "corrected_sentence, issue, better_expression, and score from 0 to 100."
            ),
        },
        {
            "role": "user",
            "content": f"Scenario: {request.scenario_id}\nLearner sentence: {request.message}",
        },
    ]


def _summary_prompt(request: SummaryRequest) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an English speaking coach. Return JSON only with keys "
                "summary, strengths, repeated_issues, better_expressions, "
                "scenario_completion, next_practice_focus, and scores. "
                "scores must include grammar, expression, fluency, "
                "scenario_completion, and overall from 0 to 100."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario: {request.scenario_id}\n"
                f"Conversation:\n{_transcript(request.messages)}\n"
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
    return FeedbackResponse(
        corrected_sentence=str(data["corrected_sentence"]),
        issue=str(data["issue"]),
        better_expression=str(data["better_expression"]),
        score=int(data["score"]),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("Expected a list.")
    return [str(item) for item in value]


def _transcript(messages: list[ChatMessage]) -> str:
    if not messages:
        return "(no prior messages)"
    return "\n".join(f"{message.role}: {message.content}" for message in messages)
