"""
Doubao (ByteDance) Streaming ASR provider.

This module proxies audio from the frontend WebSocket to the Doubao BigModel
real-time ASR API and relays transcription events back to the client.

Environment variables:
  ASR_PROVIDER_MODE    "doubao" to enable; anything else means disabled.
  DOUBAO_APP_ID        Volcano Engine app ID (10-digit number from console).
  DOUBAO_ASR_TOKEN     App-level bearer token (32 chars from console).
  DOUBAO_RESOURCE_ID   BigModel resource/endpoint ID from the console.
                       Get it from: 语音技术 → 大模型流式识别 → 接入管理.
"""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DOUBAO_ASR_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
DOUBAO_LANGUAGE = "zh-Hans-en"  # Chinese-English mixed recognition


def _load_dotenv_files() -> None:
    if os.getenv("ANYTIMESPEAK_SKIP_DOTENV", "").strip() == "1":
        return
    backend_dir = Path(__file__).resolve().parents[1]
    project_root = backend_dir.parent
    for path in [project_root / ".env", backend_dir / ".env"]:
        if path.exists():
            load_dotenv(path, override=False)


def _get_credentials() -> tuple[str, str, str]:
    """Return (app_id, token, resource_id); empty strings when missing."""
    return (
        os.getenv("DOUBAO_APP_ID", "").strip(),
        os.getenv("DOUBAO_ASR_TOKEN", "").strip(),
        os.getenv("DOUBAO_RESOURCE_ID", "").strip(),
    )


def get_asr_mode() -> str:
    """Return 'doubao' when all three required env vars are present, else 'browser'."""
    _load_dotenv_files()
    mode = os.getenv("ASR_PROVIDER_MODE", "browser").strip().lower()
    if mode == "doubao":
        app_id, token, resource_id = _get_credentials()
        if app_id and token and resource_id:
            return "doubao"
        missing = [k for k, v in [("DOUBAO_APP_ID", app_id), ("DOUBAO_ASR_TOKEN", token), ("DOUBAO_RESOURCE_ID", resource_id)] if not v]
        logger.warning(
            "ASR_PROVIDER_MODE=doubao but missing env vars: %s — falling back to browser.",
            ", ".join(missing),
        )
    return "browser"


async def proxy_doubao_asr(frontend_ws) -> None:  # type: ignore[type-arg]
    """
    Proxy audio from frontend WebSocket to Doubao ASR and relay results back.

    Frontend → backend protocol:
      - JSON text: {"type": "config", "lang": "zh-CN"}   (first frame, optional)
      - Binary:    raw PCM 16-bit 16kHz mono audio chunks
      - JSON text: {"type": "end"}                        (signal end of audio)

    Backend → frontend protocol:
      - JSON text: {"type": "ready"}
      - JSON text: {"type": "partial", "transcript": "..."}
      - JSON text: {"type": "final",   "transcript": "..."}
      - JSON text: {"type": "error",   "code": "...", "message": "..."}
    """
    try:
        import websockets  # noqa: PLC0415
    except ImportError:
        await frontend_ws.send_text(
            json.dumps({"type": "error", "code": "server-error", "message": "websockets package not installed"})
        )
        return

    _load_dotenv_files()
    app_id, token, resource_id = _get_credentials()

    if not app_id or not token or not resource_id:
        missing = [k for k, v in [("DOUBAO_APP_ID", app_id), ("DOUBAO_ASR_TOKEN", token), ("DOUBAO_RESOURCE_ID", resource_id)] if not v]
        await frontend_ws.send_text(
            json.dumps({
                "type": "error",
                "code": "not-configured",
                "message": f"Doubao ASR missing config: {', '.join(missing)}",
            })
        )
        return

    uid = f"anytimespeak_{uuid.uuid4().hex[:8]}"
    # v3/bigmodel auth headers (confirmed via official docs):
    # X-Api-App-Key, X-Api-Access-Key, X-Api-Resource-Id, X-Api-Connect-Id
    url = DOUBAO_ASR_URL
    headers = {
        "X-Api-App-Key": app_id,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": uid,
    }

    init_payload = {
        "header": {
            "app_id": app_id,
            "uid": uid,
            "namespace": "SpeechTranscription",
            "name": "StartTranscription",
        },
        "audio": {
            "format": "pcm",
            "sample_rate": 16000,
            "bits": 16,
            "channel": 1,
            "language": DOUBAO_LANGUAGE,
        },
    }

    try:
        async with websockets.connect(url, additional_headers=headers, open_timeout=8) as doubao_ws:
            await doubao_ws.send(json.dumps(init_payload))
            await frontend_ws.send_text(json.dumps({"type": "ready"}))

            stop_event = asyncio.Event()

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
                        if msg_type == "websocket.receive":
                            raw_bytes = data.get("bytes")
                            raw_text = data.get("text")
                            if raw_bytes:
                                await doubao_ws.send(raw_bytes)
                            elif raw_text:
                                try:
                                    ctrl = json.loads(raw_text)
                                    if ctrl.get("type") == "end":
                                        await doubao_ws.send(b"")
                                        break
                                except json.JSONDecodeError:
                                    pass
                finally:
                    stop_event.set()
                    try:
                        await doubao_ws.close()
                    except Exception:  # noqa: BLE001
                        pass

            async def relay_doubao_to_frontend() -> None:
                try:
                    async for raw_msg in doubao_ws:
                        if stop_event.is_set():
                            break
                        try:
                            event = json.loads(raw_msg) if isinstance(raw_msg, (str, bytes)) else {}
                        except (json.JSONDecodeError, ValueError):
                            continue

                        payload = event.get("payload", {})
                        results = payload.get("result", [])
                        if not results:
                            continue

                        for item in results:
                            text = item.get("text", "").strip()
                            if not text:
                                continue
                            is_final = bool(item.get("definite", False))
                            msg_type = "final" if is_final else "partial"
                            await frontend_ws.send_text(
                                json.dumps({"type": msg_type, "transcript": text}, ensure_ascii=False)
                            )
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
            await frontend_ws.send_text(
                json.dumps({
                    "type": "error",
                    "code": "network",
                    "message": "豆包语音识别服务暂时不可用，已切换到浏览器语音识别。",
                })
            )
        except Exception:  # noqa: BLE001
            pass
