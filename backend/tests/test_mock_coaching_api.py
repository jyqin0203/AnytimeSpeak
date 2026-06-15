from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_scenarios_endpoint_returns_mvp_scenarios():
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 3
    scenario_ids = {scenario["id"] for scenario in scenarios}
    assert {"interview", "restaurant", "meeting"}.issubset(scenario_ids)
    interview = next(scenario for scenario in scenarios if scenario["id"] == "interview")
    assert interview["scenario_id"] == "interview"
    assert interview["ai_role"] == "Hiring manager"
    assert interview["story_seed_id"]
    assert interview["story_intro_zh"]
    assert "video interview" in interview["story_intro_en"].lower()
    assert interview["opening_line"].startswith("Hi, thanks for joining today")


def test_start_session_returns_story_opening_and_empty_messages():
    response = client.post(
        "/api/sessions",
        json={"scenario_id": "meeting", "story_seed_id": "meeting_standup"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"].startswith("session_")
    assert body["scenario_id"] == "meeting"
    assert body["scenario"]["ai_role"] == "Team lead"
    assert body["story_seed_id"] == "meeting_standup"
    assert body["story_intro_zh"]
    assert body["story_intro_en"]
    assert body["opening_message"].startswith("Let's start with your update")
    assert body["messages"] == []
    assert body["created_at"]


def test_start_session_can_return_different_seeds_or_a_fixed_one():
    seed_ids = set()
    for _ in range(20):
        response = client.post("/api/sessions", json={"scenario_id": "interview"})
        assert response.status_code == 200
        seed_ids.add(response.json()["story_seed_id"])

    assert seed_ids.issubset(
        {"interview_first_round", "interview_project_dive", "interview_internship"}
    )
    assert len(seed_ids) > 1

    fixed_response = client.post(
        "/api/sessions",
        json={"scenario_id": "interview", "story_seed_id": "interview_internship"},
    )
    assert fixed_response.status_code == 200
    fixed_body = fixed_response.json()
    assert fixed_body["story_seed_id"] == "interview_internship"
    assert fixed_body["opening_message"].startswith("Hi, welcome!")


def test_chat_endpoint_returns_scenario_aware_mock_reply():
    response = client.post(
        "/api/chat",
        json={
            "scenario_id": "restaurant",
            "latest_user_message": "I want a chicken sandwich, but no onion.",
            "conversation_history": [
                {"role": "assistant", "content": "Welcome! Are you ready to order?"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "restaurant"
    assert body["session_id"]
    assert body["reply"]["role"] == "assistant"
    assert body["provider"] == "mock"
    assert "chicken sandwich" in body["reply"]["content"].lower()
    assert "onions" in body["reply"]["content"].lower()
    assert "quick_feedback" not in body


def test_feedback_endpoint_returns_correction_and_expression_tip():
    response = client.post(
        "/api/feedback",
        json={
            "scenario_id": "interview",
            "latest_user_message": "I am graduated last year and I was responsible for make the report.",
            "conversation_history": [
                {"role": "user", "content": "I want a chicken sandwich, but no onion."}
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["what_you_said"] == "I am graduated last year and I was responsible for make the report."
    assert body["recommended_english"] == (
        "I graduated last year and I was responsible for making the report."
    )
    assert "i am graduated" in body["issue"].lower()
    assert "i graduated" in body["issue"].lower()
    assert body["recommended_english"].rstrip(".!?") in body["more_natural_option"]
    assert set(body["score_breakdown"]) == {"grammar", "naturalness", "relevance", "clarity"}
    assert body["provider"] == "mock"
    assert 0 <= body["score"] <= 100


def test_feedback_endpoint_improves_recently_question_mock_quality():
    response = client.post(
        "/api/feedback",
        json={
            "scenario_id": "daily_conversation",
            "latest_user_message": "What do you do recently?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_english"] == "What have you been up to recently?"
    assert "do recently" in body["issue"]
    assert body["score_breakdown"]["relevance"] >= 80


def test_feedback_endpoint_improves_ai_project_mixed_input():
    response = client.post(
        "/api/feedback",
        json={
            "scenario_id": "daily_conversation",
            "latest_user_message": "I recently completed 2 AI 应用开发 projects.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_english"] == "I recently completed two AI application development projects."
    assert "AI application development" in body["more_natural_option"]
    assert body["score_breakdown"]["relevance"] >= 80


def test_feedback_endpoint_supports_chinese_input_with_english_suggestion():
    response = client.post(
        "/api/feedback",
        json={
            "scenario_id": "meeting",
            "latest_user_message": "我想约一个明天的会议。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "schedule a meeting" in body["recommended_english"].lower()
    assert "tomorrow" in body["recommended_english"].lower()
    assert "中文" in body["issue"]
    assert "schedule a meeting" in body["more_natural_option"]
    assert body["user_intent"] == "我想约一个明天的会议。"


def test_chat_endpoint_supports_mixed_input_without_breaking_mock_fallback():
    response = client.post(
        "/api/chat",
        json={
            "scenario_id": "meeting",
            "latest_user_message": "I want to 预约一个 meeting tomorrow.",
            "conversation_history": [
                {"role": "assistant", "content": "What progress have you made?"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "meeting"
    assert body["reply"]["role"] == "assistant"
    assert "meeting" in body["reply"]["content"].lower()
    assert "quick_feedback" not in body


def test_summary_endpoint_returns_scores_and_reusable_suggestions():
    response = client.post(
        "/api/summary",
        json={
            "scenario_id": "meeting",
            "conversation_history": [
                {
                    "role": "assistant",
                    "content": "Let's start with your update. What progress have you made?",
                },
                {
                    "role": "user",
                    "content": "I finished the page, but I have some problem with API.",
                },
                {
                    "role": "assistant",
                    "content": "What specific data fields do you need?",
                },
                {
                    "role": "user",
                    "content": "I need backend team give me the data format.",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "meeting"
    assert "会议" in body["summary"]
    assert "The main blocker is" in body["better_expressions"][0]
    scores = body["scores"]
    assert set(scores) == {
        "grammar",
        "expression",
        "fluency",
        "scenario_completion",
        "overall",
    }
    assert scores["overall"] == round(
        scores["grammar"] * 0.25
        + scores["expression"] * 0.25
        + scores["fluency"] * 0.20
        + scores["scenario_completion"] * 0.30
    )
    assert body["provider"] == "mock"
