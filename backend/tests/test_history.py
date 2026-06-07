"""Tests for password auth and practice history endpoints."""

import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

_tmp_dir = tempfile.mkdtemp()
os.environ["ANYTIMESPEAK_DB_PATH"] = str(Path(_tmp_dir) / "test.db")

import app.database as _db_module  # noqa: E402

_db_module.DB_PATH = Path(os.environ["ANYTIMESPEAK_DB_PATH"])

from app.main import app  # noqa: E402

_db_module.init_db()

client = TestClient(app)


def _register_user(username: str = "jiaying", password: str = "lover-demo-13") -> dict:
    resp = client.post("/api/users/register", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()


def _save_session(user_id: str, session_id: str = "sess_test_001", score: int = 85) -> dict:
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "scenario_id": "interview",
        "scenario_title": "面试演练",
        "story_intro_zh": "你正在参加一场面试。",
        "story_intro_en": "You are taking part in an interview.",
        "messages": [
            {"role": "assistant", "content": "Hi, please introduce yourself."},
            {"role": "user", "content": "I am a software engineer."},
        ],
        "feedbacks": [
            {
                "user_message": "I am a software engineer.",
                "feedback_json": {"issue": "Good answer.", "recommended_english": "I work as a software engineer."},
                "score": score,
            }
        ],
        "summary": {
            "summary": "You did well in the interview practice.",
            "strengths": ["Clear introduction."],
            "repeated_issues": [],
            "better_expressions": ["I work as..."],
            "scores": {"overall": score},
        },
        "scores": {"overall": score},
        "overall_score": score,
        "provider": "mock",
    }
    resp = client.post("/api/history/sessions", json=payload)
    assert resp.status_code == 200
    return resp.json()


def test_register_user_hashes_password():
    data = _register_user("alice", "safe-password")
    assert data["username"] == "alice"
    assert data["user_id"].startswith("user_")
    assert "created_at" in data

    with _db_module.get_connection() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (data["user_id"],)).fetchone()

    assert row is not None
    assert row["password_hash"] != "safe-password"
    assert row["password_hash"].startswith("pbkdf2_sha256$")


def test_register_duplicate_username_returns_409():
    _register_user("duplicate", "safe-password")
    resp = client.post("/api/users/register", json={"username": "duplicate", "password": "another-password"})
    assert resp.status_code == 409


def test_login_user_and_get_user():
    user = _register_user("bob", "correct-password")

    login = client.post("/api/users/login", json={"username": "bob", "password": "correct-password"})
    assert login.status_code == 200
    assert login.json()["user_id"] == user["user_id"]
    assert login.json()["username"] == "bob"

    fetched = client.get(f"/api/users/{user['user_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["username"] == "bob"


def test_login_with_wrong_password_returns_401():
    _register_user("carol", "correct-password")
    resp = client.post("/api/users/login", json={"username": "carol", "password": "wrong-password"})
    assert resp.status_code == 401


def test_get_nonexistent_user_returns_404():
    resp = client.get("/api/users/user_nonexistent")
    assert resp.status_code == 404


def test_save_practice_session():
    user = _register_user("diana")
    data = _save_session(user["user_id"], "sess_diana_001")
    assert data["session_id"] == "sess_diana_001"
    assert data["scenario_title"] == "面试演练"
    assert data["overall_score"] == 85
    assert data["provider"] == "mock"


def test_list_user_sessions():
    user = _register_user("eve")
    _save_session(user["user_id"], "sess_eve_001")
    _save_session(user["user_id"], "sess_eve_002")

    resp = client.get(f"/api/history/sessions?user_id={user['user_id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    session_ids = {item["session_id"] for item in items}
    assert "sess_eve_001" in session_ids
    assert "sess_eve_002" in session_ids


def test_get_session_detail():
    user = _register_user("frank")
    _save_session(user["user_id"], "sess_frank_001")

    resp = client.get("/api/history/sessions/sess_frank_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess_frank_001"
    assert data["scenario_title"] == "面试演练"
    assert len(data["messages"]) == 2
    assert len(data["feedbacks"]) == 1
    assert data["feedbacks"][0]["score"] == 85
    assert data["summary_json"]["summary"] == "You did well in the interview practice."


def test_resaving_same_session_replaces_messages_and_feedbacks():
    user = _register_user("grace")
    _save_session(user["user_id"], "sess_grace_001", score=82)
    _save_session(user["user_id"], "sess_grace_001", score=91)

    resp = client.get("/api/history/sessions/sess_grace_001")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["messages"]) == 2
    assert len(data["feedbacks"]) == 1
    assert data["overall_score"] == 91
    assert data["feedbacks"][0]["score"] == 91


def test_get_nonexistent_session_returns_404():
    resp = client.get("/api/history/sessions/sess_does_not_exist")
    assert resp.status_code == 404


def test_save_session_with_unknown_user_returns_404():
    resp = client.post(
        "/api/history/sessions",
        json={
            "user_id": "user_ghost",
            "session_id": "sess_ghost_001",
            "scenario_id": "interview",
            "scenario_title": "面试演练",
            "provider": "mock",
        },
    )
    assert resp.status_code == 404


def test_db_init_does_not_error():
    from app.database import init_db

    init_db()
