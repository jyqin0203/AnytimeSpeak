from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.history_schemas import (
    CreateGuestUserRequest,
    GuestUserResponse,
    SaveSessionRequest,
    SessionDetail,
    SessionListItem,
)
from app.history_service import (
    create_guest_user,
    get_guest_user,
    get_session_detail,
    list_user_sessions,
    save_practice_session,
)
from app.llm_provider import (
    create_chat_reply_with_fallback,
    create_feedback_with_fallback,
    create_summary_with_fallback,
)
from app.mock_service import list_scenarios
from app.mock_service import start_session
from app.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    PracticeSession,
    Scenario,
    StartSessionRequest,
    SummaryRequest,
    SummaryResponse,
)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
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


# ── Guest user endpoints ──────────────────────────────────────────────────────

@app.post("/api/users/guest", response_model=GuestUserResponse)
def post_guest_user(request: CreateGuestUserRequest):
    return create_guest_user(request)


@app.get("/api/users/{user_id}", response_model=GuestUserResponse)
def get_user(user_id: str):
    user = get_guest_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── History endpoints ─────────────────────────────────────────────────────────

@app.post("/api/history/sessions", response_model=SessionListItem)
def post_history_session(request: SaveSessionRequest):
    user = get_guest_user(request.user_id)
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
