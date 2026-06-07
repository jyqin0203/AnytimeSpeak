import httpx
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_pronunciation_assessment_mock_mode_returns_complete_shape(monkeypatch):
    monkeypatch.setenv("PRONUNCIATION_PROVIDER_MODE", "mock")
    response = client.post(
        "/api/pronunciation/assess",
        json={
            "session_id": "session_demo",
            "scenario_id": "daily_conversation",
            "user_message": "What do you do recently?",
            "transcript": "What do you do recently?",
            "reference_text": "What have you been up to recently?",
            "audio_duration_ms": 3200,
            "recognized_language": "en-US",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "heuristic_mock"
    assert body["is_fallback"] is True
    assert set(body) == {
        "provider",
        "pronunciation_score",
        "fluency_score",
        "accuracy_score",
        "completeness_score",
        "rhythm_score",
        "overall_score",
        "feedback_zh",
        "strengths",
        "improvement_tips",
        "word_tips",
        "is_fallback",
    }
    for key in (
        "pronunciation_score",
        "fluency_score",
        "accuracy_score",
        "completeness_score",
        "overall_score",
    ):
        assert 0 <= body[key] <= 100
    assert body["overall_score"] != 78
    assert body["improvement_tips"]


def test_pronunciation_assessment_empty_transcript_has_conservative_fallback(monkeypatch):
    monkeypatch.setenv("PRONUNCIATION_PROVIDER_MODE", "mock")
    response = client.post(
        "/api/pronunciation/assess",
        json={
            "scenario_id": "meeting",
            "transcript": "",
            "reference_text": "I finished the page and need the API format.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is True
    assert 50 <= body["overall_score"] <= 60
    assert "没有检测到足够语音内容" in body["feedback_zh"]


def test_pronunciation_assessment_mixed_transcript_gives_code_switching_tip(monkeypatch):
    monkeypatch.setenv("PRONUNCIATION_PROVIDER_MODE", "mock")
    response = client.post(
        "/api/pronunciation/assess",
        json={
            "scenario_id": "meeting",
            "transcript": "I want to 预约一个 meeting tomorrow",
            "reference_text": "I would like to schedule a meeting for tomorrow.",
            "recognized_language": "mixed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is True
    assert body["fluency_score"] < 82
    assert any("中英文混合" in tip for tip in body["improvement_tips"])


def test_pronunciation_assessment_api_mode_missing_key_falls_back(monkeypatch):
    monkeypatch.setenv("PRONUNCIATION_PROVIDER_MODE", "api")
    monkeypatch.delenv("PRONUNCIATION_API_KEY", raising=False)
    monkeypatch.setenv("PRONUNCIATION_API_BASE_URL", "https://example.invalid/assess")

    response = client.post(
        "/api/pronunciation/assess",
        json={
            "scenario_id": "interview",
            "transcript": "I recently completed two AI projects.",
            "reference_text": "I recently completed two AI application development projects.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "heuristic_mock"
    assert body["is_fallback"] is True


def test_pronunciation_assessment_api_failure_falls_back(monkeypatch):
    def fail_post(*_args, **_kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setenv("PRONUNCIATION_PROVIDER_MODE", "api")
    monkeypatch.setenv("PRONUNCIATION_API_KEY", "test-key")
    monkeypatch.setenv("PRONUNCIATION_API_BASE_URL", "https://example.invalid/assess")
    monkeypatch.setattr(httpx, "post", fail_post)

    response = client.post(
        "/api/pronunciation/assess",
        json={
            "scenario_id": "restaurant",
            "transcript": "Could I have a chicken sandwich with no onions?",
            "reference_text": "Could I have a chicken sandwich with no onions?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "heuristic_mock"
    assert body["is_fallback"] is True
    assert body["overall_score"] >= 75
