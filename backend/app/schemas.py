from typing import Literal

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    grammar: int = Field(ge=0, le=100)
    expression: int = Field(ge=0, le=100)
    fluency: int = Field(ge=0, le=100)
    scenario_completion: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


class FeedbackScoreBreakdown(BaseModel):
    grammar: int = Field(ge=0, le=100)
    naturalness: int = Field(ge=0, le=100)
    relevance: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)


class Scenario(BaseModel):
    id: str
    scenario_id: str
    title: str
    title_zh: str
    level: str
    ai_role: str
    user_role: str
    goal: str
    story_seed_id: str
    story_intro_zh: str
    story_intro_en: str
    opening_line: str
    opening_message: str
    conversation_style: str
    feedback_focus: list[str]
    useful_expressions: list[str]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class StartSessionRequest(BaseModel):
    scenario_id: str
    story_seed_id: str | None = None


class PracticeSession(BaseModel):
    session_id: str
    scenario_id: str
    scenario: Scenario
    story_seed_id: str
    story_intro_zh: str
    story_intro_en: str
    opening_message: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: str


class ChatRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str
    latest_user_message: str | None = None
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    messages: list[ChatMessage] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str
    latest_user_message: str | None = None
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    message: str | None = None


class FeedbackResponse(BaseModel):
    what_you_said: str
    user_intent: str
    recommended_english: str
    issue: str
    why: str
    more_natural_option: str
    score: int = Field(ge=0, le=100)
    score_breakdown: FeedbackScoreBreakdown
    provider: str = "mock"
    corrected_sentence: str | None = None
    better_expression: str | None = None
    user_intent_zh: str | None = None
    code_switching_tip: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    scenario_id: str
    reply: ChatMessage
    quick_feedback: FeedbackResponse


class SummaryRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    messages: list[ChatMessage] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    scenario_id: str
    summary: str
    strengths: list[str]
    repeated_issues: list[str]
    better_expressions: list[str]
    scenario_completion: str
    next_practice_focus: str
    code_switching_advice: str | None = None
    scores: ScoreBreakdown
    provider: str = "mock"
