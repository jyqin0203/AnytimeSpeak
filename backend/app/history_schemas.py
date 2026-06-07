from typing import Any

from pydantic import BaseModel, Field


class UserCredentialsRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    user_id: str
    username: str
    created_at: str


class MessageRecord(BaseModel):
    role: str
    content: str


class FeedbackRecord(BaseModel):
    user_message: str | None = None
    feedback_json: dict[str, Any] | None = None
    score: int | None = None


class SaveSessionRequest(BaseModel):
    user_id: str
    session_id: str
    scenario_id: str
    scenario_title: str
    story_intro_zh: str | None = None
    story_intro_en: str | None = None
    messages: list[MessageRecord] = Field(default_factory=list)
    feedbacks: list[FeedbackRecord] = Field(default_factory=list)
    summary: dict[str, Any] | None = None
    scores: dict[str, Any] | None = None
    overall_score: int | None = None
    provider: str = "mock"


class SessionListItem(BaseModel):
    session_id: str
    scenario_id: str
    scenario_title: str
    started_at: str
    overall_score: int | None = None
    summary_preview: str | None = None
    provider: str


class SessionDetail(BaseModel):
    session_id: str
    scenario_id: str
    scenario_title: str
    story_intro_zh: str | None = None
    story_intro_en: str | None = None
    started_at: str
    ended_at: str | None = None
    overall_score: int | None = None
    summary_json: dict[str, Any] | None = None
    provider: str
    messages: list[MessageRecord] = Field(default_factory=list)
    feedbacks: list[FeedbackRecord] = Field(default_factory=list)
