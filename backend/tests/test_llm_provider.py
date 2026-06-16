import logging

import pytest

from app.schemas import ChatMessage, ChatRequest, FeedbackRequest, SummaryRequest


def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LLM_PROVIDER_MODE", "OPENAI_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANYTIMESPEAK_SKIP_DOTENV", "1")


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
    assert response.provider == "mock"
    assert response.fallback_reason == "missing_api_key"
    assert response.reply.role == "assistant"
    assert "chicken sandwich" in response.reply.content.lower()
    assert not hasattr(response, "quick_feedback")


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
    assert "i am graduated" in response.issue.lower()
    assert "i graduated" in response.issue.lower()
    assert response.fallback_reason == "llm_request_failed"


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


def test_llm_api_key_env_takes_priority_over_openai_key(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "llm-test-key")
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

    llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="interview", message="I want practice.")
    )

    assert captured_headers["Authorization"] == "Bearer llm-test-key"


def test_llm_provider_loads_project_dotenv_without_printing_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.delenv("ANYTIMESPEAK_SKIP_DOTENV", raising=False)
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "LLM_PROVIDER_MODE=llm",
                "LLM_API_KEY=dotenv-test-key",
                "LLM_BASE_URL=https://example.test/v1",
                "LLM_MODEL=demo-model",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(llm_provider, "_dotenv_paths", lambda: [dotenv_path])

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

    assert response.provider == "llm"
    assert captured_headers["Authorization"] == "Bearer dotenv-test-key"


def test_llm_provider_falls_back_when_base_url_is_missing(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="interview", message="I want practice.")
    )

    assert response.provider == "mock"
    assert response.fallback_reason == "missing_base_url"


def test_llm_provider_falls_back_when_model_is_missing(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="interview", message="I want practice.")
    )

    assert response.provider == "mock"
    assert response.fallback_reason == "missing_model"


def test_llm_timeout_allows_slow_provider_responses():
    import app.llm_provider as llm_provider

    assert llm_provider.LLM_TIMEOUT_SECONDS >= 90.0


def test_chat_uses_shorter_provider_timeout():
    import app.llm_provider as llm_provider

    assert llm_provider.CHAT_TIMEOUT_SECONDS < llm_provider.LLM_TIMEOUT_SECONDS
    assert llm_provider.CHAT_TIMEOUT_SECONDS <= 30.0


def test_llm_provider_info_logs_are_enabled():
    import app.llm_provider as llm_provider

    assert llm_provider.logger.isEnabledFor(logging.INFO)


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
    assert response.provider == "llm"
    assert response.scores.overall == 85


def test_summary_accepts_string_lists_score_breakdown_and_percent_scores(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        return """
        {
          "summary": "You completed the practice.",
          "strengths": "Clear meaning; Good scenario fit",
          "repeated_issues": "Add more specific details",
          "better_expressions": "Could you tell me more about that?",
          "scenario_completion": "You handled the basic conversation.",
          "next_practice_focus": "Practice shorter answers.",
          "score_breakdown": {
            "grammar": "86%",
            "naturalness": "8/10",
            "clarity": "84",
            "relevance": 88,
            "overall": "85%"
          }
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_summary_with_fallback(
        SummaryRequest(
            scenario_id="daily_conversation",
            messages=[ChatMessage(role="user", content="I am practicing small talk.")],
        )
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.strengths == ["Clear meaning", "Good scenario fit"]
    assert response.repeated_issues == ["Add more specific details"]
    assert response.scores.expression == 80
    assert response.scores.overall == 85


def test_json_parser_accepts_markdown_code_fence_and_text():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        'Here is the result:\n```json\n{"provider":"llm","score":88}\n```\nThanks.',
        "feedback",
    )

    assert parsed == {"provider": "llm", "score": 88}


def test_json_parser_accepts_plain_json():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm('{"reply":{"role":"assistant","content":"Hi."}}', "chat")

    assert parsed == {"reply": {"role": "assistant", "content": "Hi."}}


def test_json_parser_extracts_first_valid_object_with_surrounding_text():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        'Sure, here is the JSON: {"reply":{"role":"assistant","content":"What happened?"}} Thanks.',
        "chat",
    )

    assert parsed == {"reply": {"role": "assistant", "content": "What happened?"}}


def test_json_parser_uses_first_valid_object_when_later_text_has_braces():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        'Result: {"provider":"llm","score":88} Note: {not valid json}',
        "feedback",
    )

    assert parsed == {"provider": "llm", "score": 88}


def test_json_parser_accepts_array_wrapped_object():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        '[{"provider":"llm","score":88}]',
        "feedback",
    )

    assert parsed == {"provider": "llm", "score": 88}


def test_json_parser_accepts_trailing_commas_and_smart_quotes():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        '{“provider”: “llm”, “score”: 88,}',
        "feedback",
    )

    assert parsed == {"provider": "llm", "score": 88}


def test_json_parser_accepts_simple_unquoted_keys():
    import app.llm_provider as llm_provider

    parsed = llm_provider._json_from_llm(
        '{provider: "llm", score: 88}',
        "feedback",
    )

    assert parsed == {"provider": "llm", "score": 88}


def test_feedback_falls_back_on_invalid_json_without_crashing(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")
    monkeypatch.setattr(llm_provider, "_request_chat_completion", lambda _messages: "{not valid json")

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="daily", latest_user_message="I am so 伤心.")
    )

    assert response.provider == "mock"
    assert response.fallback_reason == "json_parse_failed"
    assert response.recommended_english
    assert response.why


def test_json_parser_logs_operation_without_response_content(caplog: pytest.LogCaptureFixture):
    import app.llm_provider as llm_provider

    content = "not-json-sensitive-response"

    with caplog.at_level("WARNING"):
        with pytest.raises(llm_provider.LLMResponseParseError):
            llm_provider._json_from_llm(content, "summary")

    assert "parse_failed" in caplog.text
    assert "operation=summary" in caplog.text
    assert f"response_length={len(content)}" in caplog.text
    assert content not in caplog.text


def test_chat_repairs_missing_llm_reply_without_schema_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    monkeypatch.setattr(
        llm_provider,
        "_request_chat_completion",
        lambda _messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS: '{"reply": null}',
    )

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(scenario_id="interview", latest_user_message="I feel nervous.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.reply.content != "None"
    assert response.reply.content


def test_chat_accepts_plain_text_llm_reply_instead_of_json_parse_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS):
        return "I understand. What would you like to practice next?"

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(scenario_id="daily_conversation", latest_user_message="I want to practice.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.reply.content == "I understand. What would you like to practice next?"


def test_chat_accepts_common_content_field_without_schema_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS):
        return '{"content": "I am sorry to hear that. What happened?"}'

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(scenario_id="daily_conversation", latest_user_message="I am so sad.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.reply.content == "I am sorry to hear that. What happened?"


def test_chat_accepts_reply_text_and_normalizes_role(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS):
        return '{"reply": {"role": "ai", "text": "I hear you. What happened?"}}'

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(scenario_id="daily_conversation", latest_user_message="I am sad.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.reply.role == "assistant"
    assert response.reply.content == "I hear you. What happened?"


def test_chat_accepts_nested_reply_content_without_schema_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS):
        return '{"reply": {"content": {"text": "That sounds tough. What happened?"}}}'

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(scenario_id="daily_conversation", latest_user_message="I am sad.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.reply.content == "That sounds tough. What happened?"


def test_chat_falls_back_when_llm_repeats_previous_assistant_turn(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    repeated = "Welcome! Are you ready to order, or would you like a few recommendations first?"

    def fake_chat_completion(messages, timeout_seconds=llm_provider.LLM_TIMEOUT_SECONDS):
        return f'{{"reply": {{"role": "assistant", "content": "{repeated}"}}}}'

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_chat_reply_with_fallback(
        ChatRequest(
            scenario_id="restaurant",
            latest_user_message="A sandwich please.",
            conversation_history=[
                ChatMessage(role="assistant", content=repeated),
                ChatMessage(role="user", content="A sandwich please."),
            ],
        )
    )

    assert response.provider == "mock"
    assert response.fallback_reason == "llm_low_quality_reply"
    assert response.reply.content != repeated


def test_feedback_accepts_frontend_wording_aliases_without_schema_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        return """
        {
          "original_text": "I am so 伤心.",
          "intent": "用户想表达自己现在很伤心。",
          "recommended_expression": "I'm feeling really sad right now.",
          "main_issue": "意思表达清楚，可以把情绪词说得更自然。",
          "explanation": "你的意思表达清楚了。口语里可以用 I'm feeling really sad right now 来表达当下状态。",
          "better_version": "I've been feeling really down lately.",
          "score_breakdown": {
            "grammar": 86,
            "naturalness": 78,
            "relevance": 92,
            "clarity": 84
          },
          "provider": "llm"
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="daily_conversation", latest_user_message="I am so 伤心.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.what_you_said == "I am so 伤心."
    assert response.recommended_english == "I'm feeling really sad right now."
    assert response.more_natural_option == "I've been feeling really down lately."
    assert response.score == 85


def test_feedback_repairs_invalid_scores_without_schema_fallback(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        return """
        {
          "what_you_said": "I want something not too spicy.",
          "recommended_english": "I’d like something that isn’t too spicy.",
          "issue": "你的意思清楚，可以换成更自然的点餐表达。",
          "why": "这样说更礼貌，也更像在向服务员说明口味偏好。",
          "more_natural_option": "Could you recommend a mild dish for me?",
          "score": "N/A",
          "score_breakdown": {
            "grammar": "",
            "naturalness": null,
            "relevance": "good",
            "clarity": "8/10"
          }
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="restaurant", latest_user_message="I want something not too spicy.")
    )

    assert response.provider == "llm"
    assert response.fallback_reason is None
    assert response.score == 82
    assert response.score_breakdown.grammar == 82
    assert response.score_breakdown.naturalness == 82
    assert response.score_breakdown.relevance == 82
    assert response.score_breakdown.clarity == 80


def test_feedback_ignores_punctuation_only_voice_transcript_corrections(monkeypatch: pytest.MonkeyPatch):
    import app.llm_provider as llm_provider

    monkeypatch.setenv("LLM_PROVIDER_MODE", "llm")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")

    def fake_chat_completion(messages):
        return """
        {
          "what_you_said": "and would you like a drink",
          "user_intent": "The learner is asking about a drink.",
          "recommended_english": "And would you like a drink?",
          "issue": "首字母和句末标点需要调整。",
          "why": "加上大写和问号后更符合标点规则。",
          "more_natural_option": "And would you like a drink?",
          "score": 90,
          "score_breakdown": {
            "grammar": 90,
            "naturalness": 90,
            "relevance": 90,
            "clarity": 90
          },
          "provider": "llm"
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(scenario_id="restaurant", latest_user_message="and would you like a drink")
    )

    assert response.provider == "llm"
    assert response.recommended_english == "and would you like a drink"
    assert response.more_natural_option == "and would you like a drink"
    assert "标点" in response.why
    assert "主要问题" in response.issue


def test_chat_prompt_includes_scenario_role_goal_and_code_switching_guidance():
    import app.llm_provider as llm_provider

    messages = llm_provider._chat_prompt(
        ChatRequest(
            scenario_id="travel",
            latest_user_message="我想 check in early.",
            conversation_history=[
                ChatMessage(role="assistant", content="Hello! How can I help you with your trip today?"),
            ],
        )
    )
    prompt_text = "\n".join(message["content"] for message in messages)

    assert "story" in prompt_text.lower()
    assert "Travel service representative or helpful local guide" in prompt_text
    assert "Traveler" in prompt_text
    assert "Ask for directions or travel information" in prompt_text
    assert "clear, patient, and practical" in prompt_text.lower()
    assert "Previous conversation" in prompt_text
    assert "Latest user message: 我想 check in early." in prompt_text
    assert "Chinese-English mixed input" in prompt_text
    assert "Ask only one clear follow-up question" in prompt_text
    assert "Do not provide detailed grammar correction in the chat reply" in prompt_text
    assert "伤心" in prompt_text
    assert "first respond with empathy" in prompt_text
    assert "That sounds good" in prompt_text
    assert "quick_feedback" not in prompt_text
    assert "gently steer the conversation back" in prompt_text


def test_feedback_prompt_supports_chinese_and_mixed_input_with_chinese_explanations():
    import app.llm_provider as llm_provider

    messages = llm_provider._feedback_prompt(
        FeedbackRequest(
            scenario_id="meeting",
            latest_user_message="I want to 预约一个 meeting tomorrow.",
            conversation_history=[
                ChatMessage(role="user", content="This older turn should not be graded."),
            ],
        )
    )
    prompt_text = "\n".join(message["content"] for message in messages)

    assert "Team lead" in prompt_text
    assert "Base your analysis strictly on the latest user message" in prompt_text
    assert "This older turn should not be graded" in prompt_text
    assert "what_you_said" in prompt_text
    assert "recommended_english" in prompt_text
    assert "score_breakdown must contain integer fields grammar, naturalness, relevance" in prompt_text
    assert "中文" in prompt_text
    assert "不要羞辱用户" in prompt_text
    assert "never criticize the learner for mixing" in prompt_text
    assert "meaning is clear" in prompt_text
    assert "sad, upset, feeling down" in prompt_text


def test_summary_prompt_uses_goal_scoring_focus_and_code_switching_summary():
    import app.llm_provider as llm_provider

    messages = llm_provider._summary_prompt(
        SummaryRequest(
            scenario_id="daily_conversation",
            conversation_history=[
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
          "what_you_said": "I want to 预约一个 meeting tomorrow.",
          "user_intent": "我想约一个明天的会议。",
          "recommended_english": "I want to schedule a meeting tomorrow.",
          "issue": "中英混合表达可以理解，但需要换成完整英文。",
          "why": "schedule a meeting 是自然的会议预约表达。",
          "more_natural_option": "I'd like to schedule a meeting for tomorrow.",
          "score": 82,
          "score_breakdown": {
            "grammar": 80,
            "expression": 82,
            "fluency": 84,
            "scenario_fit": 86
          },
          "provider": "llm"
        }
        """

    monkeypatch.setattr(llm_provider, "_request_chat_completion", fake_chat_completion)

    response = llm_provider.create_feedback_with_fallback(
        FeedbackRequest(
            scenario_id="meeting",
            latest_user_message="I want to 预约一个 meeting tomorrow.",
        )
    )

    assert response.what_you_said == "I want to 预约一个 meeting tomorrow."
    assert response.user_intent == "我想约一个明天的会议。"
    assert response.recommended_english == "I want to schedule a meeting tomorrow."
    assert "schedule a meeting" in response.why
    assert response.provider == "llm"


def test_llm_text_cleanup_removes_em_dash_repeated_punctuation_and_limits_length():
    import app.llm_provider as llm_provider

    cleaned = llm_provider._clean_llm_text(
        "This is natural——but too excited!!!   Please listen??", 42
    )

    assert "—" not in cleaned
    assert " - " not in cleaned
    assert "!!!" not in cleaned
    assert "??" not in cleaned
    assert len(cleaned) <= 45


def test_llm_text_cleanup_removes_separator_hyphens():
    import app.llm_provider as llm_provider

    cleaned = llm_provider._clean_llm_text(
        "I'm nervous - this is my first interview - but I want to practice."
    )

    assert " - " not in cleaned
    assert "nervous, this" in cleaned
