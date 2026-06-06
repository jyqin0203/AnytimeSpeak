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
    assert interview["ai_role"] == "Hiring manager"
    assert interview["opening_line"].startswith("Hi, thanks for joining today")


def test_chat_endpoint_returns_scenario_aware_mock_reply():
    response = client.post(
        "/api/chat",
        json={
            "scenario_id": "restaurant",
            "messages": [
                {"role": "assistant", "content": "Welcome! Are you ready to order?"},
                {"role": "user", "content": "I want a chicken sandwich, but no onion."},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "restaurant"
    assert body["reply"]["role"] == "assistant"
    assert "chicken sandwich" in body["reply"]["content"].lower()
    assert "onions" in body["reply"]["content"].lower()
    assert body["quick_feedback"]["score"] >= 70


def test_feedback_endpoint_returns_correction_and_expression_tip():
    response = client.post(
        "/api/feedback",
        json={
            "scenario_id": "interview",
            "message": "I am graduated last year and I was responsible for make the report.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["corrected_sentence"] == (
        "I graduated last year and I was responsible for making the report."
    )
    assert "simple past" in body["issue"].lower()
    assert "I contributed to" in body["better_expression"]
    assert 0 <= body["score"] <= 100


def test_summary_endpoint_returns_scores_and_reusable_suggestions():
    response = client.post(
        "/api/summary",
        json={
            "scenario_id": "meeting",
            "messages": [
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
    assert "meeting" in body["summary"].lower()
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
