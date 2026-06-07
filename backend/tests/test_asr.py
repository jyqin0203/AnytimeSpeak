"""Tests for ASR mode endpoint and provider logic."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.asr_provider import get_asr_mode


client = TestClient(app)


# ── /api/asr/mode tests ───────────────────────────────────────────────────────

def test_asr_mode_returns_browser_when_no_env():
    """Default mode is 'browser' when env vars are absent."""
    env_patch = {"ASR_PROVIDER_MODE": "", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": ""}
    with patch.dict(os.environ, env_patch, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "browser"}


def test_asr_mode_returns_browser_when_mode_is_mock():
    """Non-doubao mode values all map to 'browser'."""
    with patch.dict(os.environ, {"ASR_PROVIDER_MODE": "mock"}, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json()["asr_mode"] == "browser"


def test_asr_mode_returns_doubao_when_fully_configured():
    """Mode is 'doubao' only when both DOUBAO_APP_ID and DOUBAO_ASR_TOKEN are set."""
    env_patch = {
        "ASR_PROVIDER_MODE": "doubao",
        "DOUBAO_APP_ID": "test_app_id",
        "DOUBAO_ASR_TOKEN": "test_token",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "doubao"}


def test_asr_mode_falls_back_to_browser_when_credentials_missing():
    """Mode falls back to 'browser' when ASR_PROVIDER_MODE=doubao but credentials absent."""
    env_patch = {
        "ASR_PROVIDER_MODE": "doubao",
        "DOUBAO_APP_ID": "",
        "DOUBAO_ASR_TOKEN": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "browser"}


# ── get_asr_mode() unit tests ─────────────────────────────────────────────────

def test_get_asr_mode_returns_browser_by_default():
    with patch.dict(os.environ, {"ASR_PROVIDER_MODE": ""}, clear=False):
        assert get_asr_mode() == "browser"


def test_get_asr_mode_returns_doubao_when_configured():
    env = {"ASR_PROVIDER_MODE": "doubao", "DOUBAO_APP_ID": "app1", "DOUBAO_ASR_TOKEN": "tok1"}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "doubao"


def test_get_asr_mode_case_insensitive():
    env = {"ASR_PROVIDER_MODE": "DOUBAO", "DOUBAO_APP_ID": "app1", "DOUBAO_ASR_TOKEN": "tok1"}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "doubao"


# ── /ws/asr endpoint smoke test ───────────────────────────────────────────────

def test_ws_asr_rejects_when_not_configured():
    """WebSocket /ws/asr should send an error and close when Doubao is not configured."""
    env_patch = {"ASR_PROVIDER_MODE": "browser", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": ""}
    with patch.dict(os.environ, env_patch, clear=False):
        with client.websocket_connect("/ws/asr") as ws:
            data = ws.receive_json()
    assert data["type"] == "error"
    assert "code" in data


def test_ws_asr_rejects_when_doubao_mode_but_no_credentials():
    """WebSocket sends error when mode=doubao but credentials are missing."""
    env_patch = {"ASR_PROVIDER_MODE": "doubao", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": ""}
    with patch.dict(os.environ, env_patch, clear=False):
        with client.websocket_connect("/ws/asr") as ws:
            data = ws.receive_json()
    assert data["type"] == "error"
