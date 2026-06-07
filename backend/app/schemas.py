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
    fallback_reason: str | None = None
    corrected_sentence: str | None = None
    better_expression: str | None = None
    user_intent_zh: str | None = None
    code_switching_tip: str | None = None


class PronunciationAssessmentRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str
    user_message: str | None = None
    transcript: str | None = None
    audio_url: str | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    audio_duration_ms: int | None = Field(default=None, ge=0)
    recognized_language: str | None = None
    reference_text: str | None = None
    provider_mode: str | None = None


class PronunciationAssessmentResponse(BaseModel):
    provider: str
    pronunciation_score: int = Field(ge=0, le=100)
    fluency_score: int = Field(ge=0, le=100)
    accuracy_score: int = Field(ge=0, le=100)
    completeness_score: int = Field(ge=0, le=100)
    rhythm_score: int | None = Field(default=None, ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    feedback_zh: str
    strengths: list[str] = Field(default_factory=list)
    improvement_tips: list[str] = Field(default_factory=list)
    word_tips: list[str] = Field(default_factory=list)
    is_fallback: bool


class ChatResponse(BaseModel):
    session_id: str
    scenario_id: str
    reply: ChatMessage
    quick_feedback: FeedbackResponse
    provider: str = "mock"
    fallback_reason: str | None = None


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
    fallback_reason: str | None = None
