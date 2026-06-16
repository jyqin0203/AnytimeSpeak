from contextlib import asynccontextmanager
import base64
import sqlite3
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.history_schemas import (
    SaveSessionRequest,
    SessionDetail,
    SessionListItem,
    UserCredentialsRequest,
    UserResponse,
)
from app.history_service import (
    get_user,
    get_session_detail,
    login_user,
    list_user_sessions,
    register_user,
    save_practice_session,
)
from app.asr_provider import get_asr_mode, proxy_doubao_asr
from app.llm_provider import (
    create_chat_reply_with_fallback,
    create_feedback_with_fallback,
    create_summary_with_fallback,
)
from app.mock_service import list_scenarios
from app.mock_service import start_session
from app.pronunciation_provider import assess_pronunciation_with_fallback, load_pronunciation_env
from app.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    PracticeSession,
    PronunciationAssessmentRequest,
    PronunciationAssessmentResponse,
    Scenario,
    StartSessionRequest,
    SummaryRequest,
    SummaryResponse,
)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    load_pronunciation_env()
    yield


app = FastAPI(title="AnytimeSpeak API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# ── ASR endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/asr/mode")
def get_asr_mode_endpoint():
    """Return the active ASR provider mode without exposing credentials."""
    return {"asr_mode": get_asr_mode()}


@app.websocket("/ws/asr")
async def websocket_asr(ws: WebSocket):
    """WebSocket endpoint: relays frontend audio to Doubao ASR and streams transcripts back."""
    await ws.accept()
    try:
        await proxy_doubao_asr(ws)
    except WebSocketDisconnect:
        pass


@app.get("/api/scenarios", response_model=list[Scenario])
def get_scenarios():
    return list_scenarios()


@app.post("/api/sessions", response_model=PracticeSession)
def post_session(request: StartSessionRequest):
    return start_session(request)


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    return create_chat_reply_with_fallback(request)


@app.post("/api/feedback", response_model=FeedbackResponse)
def post_feedback(request: FeedbackRequest):
    return create_feedback_with_fallback(request)


@app.post("/api/summary", response_model=SummaryResponse)
def post_summary(request: SummaryRequest):
    return create_summary_with_fallback(request)


@app.post("/api/pronunciation/assess", response_model=PronunciationAssessmentResponse)
async def post_pronunciation_assessment(
    raw_request: Request,
):
    content_type = raw_request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await raw_request.form()
        audio = form.get("audio")
        if audio is None or not hasattr(audio, "read"):
            raise HTTPException(status_code=422, detail="audio file is required")
        audio_bytes = await audio.read()
        scenario_id = _form_str(form, "scenario_id")
        if not scenario_id:
            raise HTTPException(status_code=422, detail="scenario_id is required")
        request = PronunciationAssessmentRequest(
            session_id=_form_str(form, "session_id"),
            scenario_id=scenario_id,
            user_message=_form_str(form, "user_message"),
            transcript=_form_str(form, "transcript"),
            audio_base64=base64.b64encode(audio_bytes).decode("ascii"),
            audio_format=_form_str(form, "audio_format") or getattr(audio, "content_type", None) or getattr(audio, "filename", None),
            audio_duration_ms=_form_int(form, "audio_duration_ms"),
            recognized_language=_form_str(form, "recognized_language"),
            reference_text=_form_str(form, "reference_text"),
            provider_mode=_form_str(form, "provider_mode"),
        )
        return await assess_pronunciation_with_fallback(request)

    payload = await raw_request.json()
    return await assess_pronunciation_with_fallback(PronunciationAssessmentRequest(**payload))


def _form_str(form, key: str) -> str | None:
    value = form.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _form_int(form, key: str) -> int | None:
    value = _form_str(form, key)
    if value is None:
        return None
    return int(value)


# ── Guest user endpoints ──────────────────────────────────────────────────────

@app.post("/api/users/register", response_model=UserResponse)
def post_register_user(request: UserCredentialsRequest):
    try:
        return register_user(request)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc


@app.post("/api/users/login", response_model=UserResponse)
def post_login_user(request: UserCredentialsRequest):
    user = login_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return user


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str):
    user = get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── History endpoints ─────────────────────────────────────────────────────────

@app.post("/api/history/sessions", response_model=SessionListItem)
def post_history_session(request: SaveSessionRequest):
    user = get_user(request.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return save_practice_session(request)


@app.get("/api/history/sessions", response_model=list[SessionListItem])
def get_history_sessions(user_id: str):
    return list_user_sessions(user_id)


@app.get("/api/history/sessions/{session_id}", response_model=SessionDetail)
def get_history_session(session_id: str):
    detail = get_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail
