import pytest

from app.schemas import ChatMessage, ChatRequest, FeedbackRequest, SummaryRequest


def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LLM_PROVIDER_MODE", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_chat_fallback_stays_mock_when_llm_env_is_missing(monkeypatch: pytest.MonkeyPatch):
    from app.llm_provider import create_chat_reply_with_fallback

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")

    response = create_chat_reply_with_fallback(
        ChatRequest(
            scenario_id="restaurant",
            messages=[
                ChatMessage(role="user", content="I want a chicken sandwich, but no onion.")
            ],
        )
    )

    assert response.scenario_id == "restaurant"
    assert response.reply.role == "assistant"
    assert "chicken sandwich" in response.reply.content.lower()
    assert response.quick_feedback.score >= 70


def test_feedback_falls_back_to_mock_when_llm_call_fails(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def raise_provider_error(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm_provider, "_request_chat_completion", raise_provider_error)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(
            scenario_id="interview",
            message="I am graduated last year and I was responsible for make the report.",
        )
    )

    assert response.corrected_sentence == (
        "I graduated last year and I was responsible for making the report."
    )
    assert "simple past" in response.issue.lower()


def test_summary_uses_llm_when_mode_and_config_are_complete(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        assert any("Return JSON only" in message["content"] for message in messages)
        return """
        {
          "summary": "You handled the meeting clearly.",
          "strengths": ["Clear update"],
          "repeated_issues": ["Add more detail"],
          "better_expressions": ["The main blocker is the API response format."],
          "scenario_completion": "You covered the main meeting goal.",
          "next_practice_focus": "Practice concise status updates.",
          "scores": {
            "grammar": 86,
            "expression": 84,
            "fluency": 82,
            "scenario_completion": 88,
            "overall": 85
          }
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_summary_with_fallback(
        SummaryRequest(
            scenario_id="meeting",
            messages=[ChatMessage(role="user", content="I finished the page and need API help.")],
        )
    )

    assert response.scenario_id == "meeting"
    assert response.summary == "You handled the meeting clearly."
    assert response.scores.overall == 85
