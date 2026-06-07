"""Tests for guest user and practice history endpoints."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point the DB at a temp file so tests never write to the real DB.
_tmp_dir = tempfile.mkdtemp()
os.environ["ANYTIMESPEAK_DB_PATH"] = str(Path(_tmp_dir) / "test.db")

# Patch DB_PATH before importing the app so the temp path is used.
import app.database as _db_module  # noqa: E402

_db_module.DB_PATH = Path(os.environ["ANYTIMESPEAK_DB_PATH"])
_db_module.DB_DIR = _db_module.DB_PATH.parent

from app.main import app  # noqa: E402

_db_module.init_db()

client = TestClient(app)


# ── helpers ────────────────────────────────────────────────────────────────────

def _create_user(name: str = "Jiaying") -> dict:
    resp = client.post("/api/users/guest", json={"display_name": name})
    assert resp.status_code == 200
    return resp.json()


def _save_session(user_id: str, session_id: str = "sess_test_001") -> dict:
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "scenario_id": "interview",
        "scenario_title": "面试沟通",
        "story_intro_zh": "你正在参加一场面试。",
        "story_intro_en": "You are taking part in an interview.",
        "messages": [
            {"role": "assistant", "content": "Hi, please introduce yourself."},
            {"role": "user", "content": "I am a software engineer."},
        ],
        "feedbacks": [
            {
                "user_message": "I am a software engineer.",
                "feedback_json": {"issue": "Good answer."},
                "score": 85,
            }
        ],
        "summary": {
            "summary": "You did well in the interview practice.",
            "strengths": ["Clear introduction."],
            "repeated_issues": [],
            "better_expressions": [],
        },
        "scores": {"overall": 85},
        "overall_score": 85,
        "provider": "mock",
    }
    resp = client.post("/api/history/sessions", json=payload)
    assert resp.status_code == 200
    return resp.json()


# ── tests ──────────────────────────────────────────────────────────────────────

def test_create_guest_user():
    data = _create_user("Alice")
    assert data["display_name"] == "Alice"
    assert data["user_id"].startswith("user_")
    assert "created_at" in data


def test_get_guest_user():
    user = _create_user("Bob")
    resp = client.get(f"/api/users/{user['user_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Bob"
    assert data["user_id"] == user["user_id"]


def test_get_nonexistent_user_returns_404():
    resp = client.get("/api/users/user_nonexistent")
    assert resp.status_code == 404


def test_save_practice_session():
    user = _create_user("Charlie")
    data = _save_session(user["user_id"], "sess_charlie_001")
    assert data["session_id"] == "sess_charlie_001"
    assert data["scenario_title"] == "面试沟通"
    assert data["overall_score"] == 85
    assert data["provider"] == "mock"


def test_list_user_sessions():
    user = _create_user("Diana")
    _save_session(user["user_id"], "sess_diana_001")
    _save_session(user["user_id"], "sess_diana_002")

    resp = client.get(f"/api/history/sessions?user_id={user['user_id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    session_ids = {item["session_id"] for item in items}
    assert "sess_diana_001" in session_ids
    assert "sess_diana_002" in session_ids


def test_get_session_detail():
    user = _create_user("Eve")
    _save_session(user["user_id"], "sess_eve_001")

    resp = client.get("/api/history/sessions/sess_eve_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess_eve_001"
    assert data["scenario_title"] == "面试沟通"
    assert len(data["messages"]) == 2
    assert len(data["feedbacks"]) == 1
    assert data["feedbacks"][0]["score"] == 85
    assert data["summary_json"]["summary"] == "You did well in the interview practice."


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
            "scenario_title": "面试沟通",
            "provider": "mock",
        },
    )
    assert resp.status_code == 404


def test_db_init_does_not_error():
    from app.database import init_db
    init_db()  # calling twice should be idempotent
