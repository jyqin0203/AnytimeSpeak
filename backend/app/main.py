from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.llm_provider import (
    create_chat_reply_with_fallback,
    create_feedback_with_fallback,
    create_summary_with_fallback,
)
from app.mock_service import list_scenarios
from app.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    Scenario,
    SummaryRequest,
    SummaryResponse,
)

app = FastAPI(title="AnytimeSpeak API")

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


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    return create_chat_reply_with_fallback(request)


@app.post("/api/feedback", response_model=FeedbackResponse)
def post_feedback(request: FeedbackRequest):
    return create_feedback_with_fallback(request)


@app.post("/api/summary", response_model=SummaryResponse)
def post_summary(request: SummaryRequest):
    return create_summary_with_fallback(request)
