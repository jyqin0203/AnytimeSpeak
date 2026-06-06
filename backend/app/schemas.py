from typing import Literal

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    id: str
    title: str
    title_zh: str
    level: str
    ai_role: str
    user_role: str
    goal: str
    opening_line: str
    conversation_style: str
    feedback_focus: list[str]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    scenario_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    scenario_id: str
    message: str = Field(min_length=1)


class FeedbackResponse(BaseModel):
    corrected_sentence: str
    issue: str
    better_expression: str
    user_intent_zh: str | None = None
    code_switching_tip: str | None = None
    score: int = Field(ge=0, le=100)


class ChatResponse(BaseModel):
    scenario_id: str
    reply: ChatMessage
    quick_feedback: FeedbackResponse


class SummaryRequest(BaseModel):
    scenario_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    grammar: int = Field(ge=0, le=100)
    expression: int = Field(ge=0, le=100)
    fluency: int = Field(ge=0, le=100)
    scenario_completion: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


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
