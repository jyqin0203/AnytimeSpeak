import pytest

from app.schemas import ChatMessage, ChatRequest, FeedbackRequest, SummaryRequest


def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LLM_PROVIDER_MODE", "OPENAI_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
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


def test_llm_provider_uses_openai_api_key_env(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    captured_headers = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"corrected_sentence":"OK","issue":"说明","better_expression":"OK","score":90}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        captured_headers.update(headers)
        return FakeResponse()

    monkeypatch.setattr(llm_provider.httpx, "post", fake_post)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="interview", message="I want practice.")
    )

    assert captured_headers["Authorization"] == "Bearer openai-test-key"
    assert response.score == 90


def test_llm_provider_defaults_to_qwen_plus_on_alibaba_bailian(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "dashscope-test-key")

    captured_request = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"corrected_sentence":"OK","issue":"说明","better_expression":"OK","score":90}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        captured_request["url"] = url
        captured_request["json"] = json
        captured_request["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(llm_provider.httpx, "post", fake_post)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="interview", message="I want practice.")
    )

    assert captured_request["url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    assert captured_request["json"]["model"] == "qwen-plus"
    assert captured_request["headers"]["Authorization"] == "Bearer dashscope-test-key"
    assert response.score == 90


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


def test_chat_prompt_includes_scenario_role_goal_and_code_switching_guidance():
    import app.llm_provider as llm_provider

    messages = llm_provider._chat_prompt(
        ChatRequest(
            scenario_id="travel",
            messages=[ChatMessage(role="user", content="我想 check in early.")],
        )
    )
    prompt_text = "\n".join(message["content"] for message in messages)

    assert "Travel service representative or helpful local guide" in prompt_text
    assert "Traveler" in prompt_text
    assert "Ask for directions or travel information" in prompt_text
    assert "clear, patient, and practical" in prompt_text.lower()
    assert "Chinese-English mixed input" in prompt_text
    assert "continue the conversation naturally" in prompt_text


def test_feedback_prompt_supports_chinese_and_mixed_input_with_chinese_explanations():
    import app.llm_provider as llm_provider

    messages = llm_provider._feedback_prompt(
        FeedbackRequest(
            scenario_id="meeting",
            message="I want to 预约一个 meeting tomorrow.",
        )
    )
    prompt_text = "\n".join(message["content"] for message in messages)

    assert "Team lead" in prompt_text
    assert "user_intent_zh" in prompt_text
    assert "code_switching_tip" in prompt_text
    assert "中文" in prompt_text
    assert "不要羞辱用户" in prompt_text


def test_summary_prompt_uses_goal_scoring_focus_and_code_switching_summary():
    import app.llm_provider as llm_provider

    messages = llm_provider._summary_prompt(
        SummaryRequest(
            scenario_id="daily_conversation",
            messages=[
                ChatMessage(role="user", content="Today is good."),
                ChatMessage(role="user", content="我 after work watch movie."),
            ],
        )
    )
    prompt_text = "\n".join(message["content"] for message in messages)

    assert "Friendly conversation partner" in prompt_text
    assert "Build comfort with casual English conversation" in prompt_text
    assert "basic tense, articles, and sentence structure" in prompt_text
    assert "中英转换建议" in prompt_text
    assert "summary mostly in Chinese" in prompt_text


def test_feedback_response_parses_code_switching_fields_when_llm_returns_them(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        return """
        {
          "corrected_sentence": "I want to schedule a meeting tomorrow.",
          "issue": "你想表达预约会议，核心意思很清楚。",
          "better_expression": "I'd like to schedule a meeting for tomorrow.",
          "user_intent_zh": "我想约一个明天的会议。",
          "code_switching_tip": "把“预约一个 meeting”整体换成 schedule a meeting。",
          "score": 82
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(
            scenario_id="meeting",
            message="I want to 预约一个 meeting tomorrow.",
        )
    )

    assert response.user_intent_zh == "我想约一个明天的会议。"
    assert "schedule a meeting" in response.code_switching_tip
