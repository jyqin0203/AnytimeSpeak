"""Tests for ASR mode endpoint and provider logic."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.asr_provider import get_asr_mode


client = TestClient(app)

_ALL_THREE = {
    "ASR_PROVIDER_MODE": "doubao",
    "DOUBAO_APP_ID": "test_app_id",
    "DOUBAO_ASR_TOKEN": "test_token_32c",
    "DOUBAO_RESOURCE_ID": "test_resource_id",
}


# ── /api/asr/mode tests ───────────────────────────────────────────────────────

def test_asr_mode_returns_browser_when_no_env():
    """Default mode is 'browser' when env vars are absent."""
    env_patch = {"ASR_PROVIDER_MODE": "", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": "", "DOUBAO_RESOURCE_ID": ""}
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
    """Mode is 'doubao' only when all three vars (APP_ID, TOKEN, RESOURCE_ID) are set."""
    with patch.dict(os.environ, _ALL_THREE, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "doubao"}


def test_asr_mode_falls_back_when_resource_id_missing():
    """Mode falls back to 'browser' when DOUBAO_RESOURCE_ID is absent."""
    env_patch = {
        "ASR_PROVIDER_MODE": "doubao",
        "DOUBAO_APP_ID": "app1",
        "DOUBAO_ASR_TOKEN": "tok1",
        "DOUBAO_RESOURCE_ID": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "browser"}


def test_asr_mode_falls_back_to_browser_when_credentials_missing():
    """Mode falls back to 'browser' when APP_ID and TOKEN are absent."""
    env_patch = {
        "ASR_PROVIDER_MODE": "doubao",
        "DOUBAO_APP_ID": "",
        "DOUBAO_ASR_TOKEN": "",
        "DOUBAO_RESOURCE_ID": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        response = client.get("/api/asr/mode")
    assert response.status_code == 200
    assert response.json() == {"asr_mode": "browser"}


# ── get_asr_mode() unit tests ─────────────────────────────────────────────────

def test_get_asr_mode_returns_browser_by_default():
    env = {"ASR_PROVIDER_MODE": "", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": "", "DOUBAO_RESOURCE_ID": ""}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "browser"


def test_get_asr_mode_returns_doubao_when_fully_configured():
    with patch.dict(os.environ, _ALL_THREE, clear=False):
        assert get_asr_mode() == "doubao"


def test_get_asr_mode_case_insensitive():
    env = {**_ALL_THREE, "ASR_PROVIDER_MODE": "DOUBAO"}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "doubao"


def test_get_asr_mode_browser_when_resource_id_missing():
    env = {"ASR_PROVIDER_MODE": "doubao", "DOUBAO_APP_ID": "app1", "DOUBAO_ASR_TOKEN": "tok1", "DOUBAO_RESOURCE_ID": ""}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "browser"


# ── /ws/asr endpoint smoke tests ─────────────────────────────────────────────

def test_ws_asr_rejects_when_not_configured():
    """WebSocket /ws/asr sends error when Doubao is not configured."""
    env_patch = {"ASR_PROVIDER_MODE": "browser", "DOUBAO_APP_ID": "", "DOUBAO_ASR_TOKEN": "", "DOUBAO_RESOURCE_ID": ""}
    with patch.dict(os.environ, env_patch, clear=False):
        with client.websocket_connect("/ws/asr") as ws:
            data = ws.receive_json()
    assert data["type"] == "error"
    assert "code" in data


def test_ws_asr_rejects_when_resource_id_missing():
    """WebSocket sends error when resource_id is absent."""
    env_patch = {
        "ASR_PROVIDER_MODE": "doubao",
        "DOUBAO_APP_ID": "app1",
        "DOUBAO_ASR_TOKEN": "tok1",
        "DOUBAO_RESOURCE_ID": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        with client.websocket_connect("/ws/asr") as ws:
            data = ws.receive_json()
    assert data["type"] == "error"
