"""
Doubao (ByteDance) BigModel Streaming ASR provider.

This module proxies PCM audio from the frontend WebSocket to the Doubao
BigModel real-time ASR API and relays transcription events back to the client.

Environment variables:
  ASR_PROVIDER_MODE    "doubao" to enable; anything else means disabled.
  DOUBAO_API_KEY       New console APP Key / X-Api-Key.
  DOUBAO_APP_ID        Legacy console app ID / X-Api-App-Key.
  DOUBAO_ASR_TOKEN     Legacy console access token / X-Api-Access-Key.
  DOUBAO_RESOURCE_ID   BigModel resource ID / X-Api-Resource-Id.
  DOUBAO_ASR_URL       Optional WebSocket URL; defaults to bigmodel_async.
  DOUBAO_RESULT_TYPE   Optional: "full" (default) or "single".
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DOUBAO_DEFAULT_ASR_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async"
DOUBAO_LANGUAGE = "zh-Hans-en"  # Chinese-English mixed recognition.
DOUBAO_DEFAULT_RESULT_TYPE = "full"


def _load_dotenv_files() -> None:
    if os.getenv("ANYTIMESPEAK_SKIP_DOTENV", "").strip() == "1":
        return
    backend_dir = Path(__file__).resolve().parents[1]
    project_root = backend_dir.parent
    for path in [project_root / ".env", backend_dir / ".env"]:
        if path.exists():
            load_dotenv(path, override=False)


def _get_credentials() -> tuple[str, str, str, str]:
    """Return (api_key, app_id, token, resource_id); empty strings when missing."""
    return (
        os.getenv("DOUBAO_API_KEY", "").strip(),
        os.getenv("DOUBAO_APP_ID", "").strip(),
        os.getenv("DOUBAO_ASR_TOKEN", "").strip(),
        os.getenv("DOUBAO_RESOURCE_ID", "").strip(),
    )


def _has_doubao_auth(api_key: str, app_id: str, token: str, resource_id: str) -> bool:
    """New console uses API key; legacy console uses app ID plus access token."""
    return bool(resource_id and (api_key or (app_id and token)))


def _get_doubao_asr_url() -> str:
    url = os.getenv("DOUBAO_ASR_URL", "").strip()
    return url or DOUBAO_DEFAULT_ASR_URL


def _get_result_type() -> str:
    result_type = os.getenv("DOUBAO_RESULT_TYPE", DOUBAO_DEFAULT_RESULT_TYPE).strip().lower()
    if result_type in {"full", "single"}:
        return result_type
    logger.warning("Invalid DOUBAO_RESULT_TYPE=%s; falling back to full.", result_type)
    return DOUBAO_DEFAULT_RESULT_TYPE


def get_asr_mode() -> str:
    """Return 'doubao' when all required env vars are present, else 'browser'."""
    _load_dotenv_files()
    mode = os.getenv("ASR_PROVIDER_MODE", "browser").strip().lower()
    if mode == "doubao":
        api_key, app_id, token, resource_id = _get_credentials()
        if _has_doubao_auth(api_key, app_id, token, resource_id):
            return "doubao"
        missing = [
            key
            for key, value in [
                ("DOUBAO_RESOURCE_ID", resource_id),
                ("DOUBAO_API_KEY or DOUBAO_APP_ID+DOUBAO_ASR_TOKEN", api_key or (app_id and token)),
            ]
            if not value
        ]
        logger.warning("ASR_PROVIDER_MODE=doubao but missing env vars: %s; falling back to browser.", ", ".join(missing))
    return "browser"


def _build_doubao_request_params(uid: str, app_id: str = "") -> dict:
    """Build the BigModel ASR init payload used inside the V3 binary frame."""
    params = {
        "user": {"uid": uid},
        "audio": {
            "format": "pcm",
            "codec": "raw",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
            "language": DOUBAO_LANGUAGE,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": True,
            "result_type": _get_result_type(),
            "show_utterances": True,
            "corpus": {"correct_table_name": "", "context": ""},
        },
    }
    if app_id:
        params["app"] = {"appid": app_id, "cluster": "volcengine_input_common"}
    return params


def _build_doubao_headers(
    *,
    api_key: str,
    app_id: str,
    token: str,
    resource_id: str,
    request_id: str,
) -> dict[str, str]:
    """Build V3 ASR authentication headers for both new and legacy consoles."""
    headers = {
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
        "X-Api-Sequence": "-1",
    }
    if api_key:
        headers["X-Api-Key"] = api_key
    if app_id and token:
        headers["X-Api-App-Key"] = app_id
        headers["X-Api-Access-Key"] = token
    return headers


def _extract_transcript_events(parsed: dict) -> list[tuple[str, str]]:
    """Return frontend event tuples: ('partial'|'final', transcript)."""
    message = parsed.get("message")
    if not isinstance(message, dict):
        return []

    results = message.get("result") or message.get("results") or []
    if isinstance(results, dict):
        results = [results]
    if not isinstance(results, list):
        return []

    events: list[tuple[str, str]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        utterances = item.get("utterances") or []
        utterance_is_final = (
            isinstance(utterances, list)
            and any(isinstance(utterance, dict) and bool(utterance.get("definite", False)) for utterance in utterances)
        )
        msg_type = "final" if bool(item.get("definite", False)) or utterance_is_final or bool(parsed.get("is_last_package")) else "partial"
        events.append((msg_type, text))
    return events


async def proxy_doubao_asr(frontend_ws) -> None:  # type: ignore[type-arg]
    """
    Proxy audio from frontend WebSocket to Doubao ASR and relay results back.

    Frontend -> backend protocol:
      - JSON text: {"type": "config", "lang": "zh-CN"} (first frame, optional)
      - Binary: raw PCM 16-bit 16kHz mono audio chunks
      - JSON text: {"type": "end"} (signal end of audio)

    Backend -> frontend protocol:
      - JSON: {"type": "ready"}
      - JSON: {"type": "partial", "transcript": "..."}
      - JSON: {"type": "final", "transcript": "..."}
      - JSON: {"type": "error", "code": "...", "message": "..."}
    """
    try:
        import websockets  # noqa: PLC0415
        from volcengine_audio.stt import VolcengineAsrFunctionsV3  # noqa: PLC0415
    except ImportError as exc:
        await frontend_ws.send_json(
            {
                "type": "error",
                "code": "server-error",
                "message": f"Doubao ASR dependency not installed: {exc.name}",
            }
        )
        return

    _load_dotenv_files()
    api_key, app_id, token, resource_id = _get_credentials()

    if not _has_doubao_auth(api_key, app_id, token, resource_id):
        missing = [
            key
            for key, value in [
                ("DOUBAO_RESOURCE_ID", resource_id),
                ("DOUBAO_API_KEY or DOUBAO_APP_ID+DOUBAO_ASR_TOKEN", api_key or (app_id and token)),
            ]
            if not value
        ]
        await frontend_ws.send_json(
            {
                "type": "error",
                "code": "not-configured",
                "message": f"Doubao ASR missing config: {', '.join(missing)}",
            }
        )
        return

    uid = f"anytimespeak_{uuid.uuid4().hex[:8]}"
    request_id = str(uuid.uuid4())
    headers = _build_doubao_headers(
        api_key=api_key,
        app_id=app_id,
        token=token,
        resource_id=resource_id,
        request_id=request_id,
    )

    try:
        async with websockets.connect(_get_doubao_asr_url(), additional_headers=headers, open_timeout=8) as doubao_ws:
            sequence = 1
            init_frame = bytes(
                VolcengineAsrFunctionsV3.generate_asr_full_client_request(
                    sequence=sequence,
                    request_params=_build_doubao_request_params(uid=uid, app_id=app_id),
                    compression=True,
                )
            )
            await doubao_ws.send(init_frame)
            await frontend_ws.send_json({"type": "ready"})

            stop_event = asyncio.Event()
            sequence_lock = asyncio.Lock()

            async def next_sequence() -> int:
                nonlocal sequence
                async with sequence_lock:
                    sequence += 1
                    return sequence

            async def relay_frontend_to_doubao() -> None:
                try:
                    while not stop_event.is_set():
                        try:
                            data = await asyncio.wait_for(frontend_ws.receive(), timeout=30.0)
                        except asyncio.TimeoutError:
                            break

                        msg_type = data.get("type", "")
                        if msg_type == "websocket.disconnect":
                            break
                        if msg_type != "websocket.receive":
                            continue

                        raw_bytes = data.get("bytes")
                        raw_text = data.get("text")
                        if raw_bytes:
                            audio_frame = bytes(
                                VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
                                    sequence=await next_sequence(),
                                    audio=raw_bytes,
                                )
                            )
                            await doubao_ws.send(audio_frame)
                        elif raw_text:
                            try:
                                ctrl = json.loads(raw_text)
                            except json.JSONDecodeError:
                                continue
                            if ctrl.get("type") == "end":
                                end_frame = bytes(
                                    VolcengineAsrFunctionsV3.generate_asr_audio_only_request(
                                        sequence=await next_sequence(),
                                        audio=b"",
                                    )
                                )
                                await doubao_ws.send(end_frame)
                                break
                finally:
                    pass

            async def relay_doubao_to_frontend() -> None:
                try:
                    async for raw_msg in doubao_ws:
                        if stop_event.is_set():
                            break
                        try:
                            parsed = VolcengineAsrFunctionsV3.parse_response(bytes(raw_msg))
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Failed to parse Doubao ASR frame: %s: %s", type(exc).__name__, exc)
                            continue

                        if parsed.get("code"):
                            await frontend_ws.send_json(
                                {
                                    "type": "error",
                                    "code": "provider-error",
                                    "message": str(parsed.get("message") or parsed.get("code")),
                                }
                            )
                            break

                        for msg_type, text in _extract_transcript_events(parsed):
                            await frontend_ws.send_json({"type": msg_type, "transcript": text})

                        if parsed.get("is_last_package"):
                            break
                finally:
                    stop_event.set()

            await asyncio.gather(
                relay_frontend_to_doubao(),
                relay_doubao_to_frontend(),
                return_exceptions=True,
            )

    except Exception as exc:  # noqa: BLE001
        logger.warning("Doubao ASR proxy error: %s: %s", type(exc).__name__, exc)
        try:
            await frontend_ws.send_json(
                {
                    "type": "error",
                    "code": "network",
                    "message": "Doubao speech recognition is temporarily unavailable; switched back to browser speech recognition.",
                }
            )
        except Exception:  # noqa: BLE001
            pass
