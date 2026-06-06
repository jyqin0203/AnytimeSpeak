from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mock_service import create_chat_reply, create_feedback, create_summary, list_scenarios
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
    return create_chat_reply(request)


@app.post("/api/feedback", response_model=FeedbackResponse)
def post_feedback(request: FeedbackRequest):
    return create_feedback(request)


@app.post("/api/summary", response_model=SummaryResponse)
def post_summary(request: SummaryRequest):
    return create_summary(request)
