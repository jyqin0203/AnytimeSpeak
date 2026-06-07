"""Tests for ASR mode endpoint and provider logic."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.asr_provider import (
    _build_doubao_headers,
    _build_doubao_request_params,
    _extract_transcript_events,
    _get_doubao_asr_url,
    get_asr_mode,
)


client = TestClient(app)

_ALL_THREE = {
    "ASR_PROVIDER_MODE": "doubao",
    "DOUBAO_APP_ID": "test_app_id",
    "DOUBAO_ASR_TOKEN": "test_token_32c",
    "DOUBAO_RESOURCE_ID": "test_resource_id",
}

_NEW_CONSOLE = {
    "ASR_PROVIDER_MODE": "doubao",
    "DOUBAO_API_KEY": "test_api_key",
    "DOUBAO_APP_ID": "",
    "DOUBAO_ASR_TOKEN": "",
    "DOUBAO_RESOURCE_ID": "volc.seedasr.sauc.duration",
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


def test_asr_mode_returns_doubao_with_new_console_api_key():
    """New console credentials only require API key plus resource ID."""
    with patch.dict(os.environ, _NEW_CONSOLE, clear=False):
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


def test_get_asr_mode_returns_doubao_with_new_console_api_key():
    with patch.dict(os.environ, _NEW_CONSOLE, clear=False):
        assert get_asr_mode() == "doubao"


def test_get_asr_mode_case_insensitive():
    env = {**_ALL_THREE, "ASR_PROVIDER_MODE": "DOUBAO"}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "doubao"


def test_get_asr_mode_browser_when_resource_id_missing():
    env = {"ASR_PROVIDER_MODE": "doubao", "DOUBAO_APP_ID": "app1", "DOUBAO_ASR_TOKEN": "tok1", "DOUBAO_RESOURCE_ID": ""}
    with patch.dict(os.environ, env, clear=False):
        assert get_asr_mode() == "browser"


def test_doubao_request_params_default_to_bigmodel_full_result():
    with patch.dict(os.environ, {"DOUBAO_RESULT_TYPE": ""}, clear=False):
        params = _build_doubao_request_params(uid="user1", app_id="app1")

    assert params["request"]["model_name"] == "bigmodel"
    assert params["request"]["result_type"] == "full"
    assert params["audio"]["format"] == "pcm"
    assert params["audio"]["rate"] == 16000
    assert params["app"]["appid"] == "app1"


def test_doubao_request_params_accept_single_result_type():
    with patch.dict(os.environ, {"DOUBAO_RESULT_TYPE": "single"}, clear=False):
        params = _build_doubao_request_params(uid="user1")

    assert params["request"]["result_type"] == "single"
    assert "app" not in params


def test_doubao_headers_use_new_console_api_key():
    headers = _build_doubao_headers(
        api_key="api-key",
        app_id="",
        token="",
        resource_id="volc.seedasr.sauc.duration",
        request_id="request-1",
    )

    assert headers == {
        "X-Api-Key": "api-key",
        "X-Api-Resource-Id": "volc.seedasr.sauc.duration",
        "X-Api-Request-Id": "request-1",
        "X-Api-Sequence": "-1",
    }


def test_doubao_headers_keep_legacy_console_auth():
    headers = _build_doubao_headers(
        api_key="",
        app_id="app-id",
        token="access-token",
        resource_id="volc.bigasr.sauc.duration",
        request_id="request-2",
    )

    assert headers["X-Api-App-Key"] == "app-id"
    assert headers["X-Api-Access-Key"] == "access-token"
    assert headers["X-Api-Resource-Id"] == "volc.bigasr.sauc.duration"
    assert headers["X-Api-Request-Id"] == "request-2"
    assert headers["X-Api-Sequence"] == "-1"


def test_doubao_asr_url_defaults_to_async_endpoint():
    with patch.dict(os.environ, {"DOUBAO_ASR_URL": ""}, clear=False):
        assert _get_doubao_asr_url().endswith("/api/v3/sauc/bigmodel_async")


def test_doubao_asr_url_can_override_endpoint():
    with patch.dict(os.environ, {"DOUBAO_ASR_URL": "wss://example.test/asr"}, clear=False):
        assert _get_doubao_asr_url() == "wss://example.test/asr"


def test_extract_transcript_events_maps_definite_to_final():
    parsed = {
        "message": {
            "result": [
                {"text": "hel", "definite": False},
                {"text": "hello", "definite": True},
            ]
        }
    }

    assert _extract_transcript_events(parsed) == [("partial", "hel"), ("final", "hello")]


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
