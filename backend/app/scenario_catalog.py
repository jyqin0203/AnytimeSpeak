from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioPromptConfig:
    scenario_id: str
    title_zh: str
    title_en: str
    level: str
    ai_role: str
    user_role: str
    goal: str
    opening_message: str
    conversation_style: str
    feedback_focus: list[str]
    useful_expressions: list[str]
    scoring_focus: list[str]


SCENARIO_PROMPT_CONFIGS: dict[str, ScenarioPromptConfig] = {
    "interview": ScenarioPromptConfig(
        scenario_id="interview",
        title_zh="面试",
        title_en="Interview",
        level="Intermediate to upper-intermediate",
        ai_role="Hiring manager",
        user_role="Job candidate",
        goal=(
            "Give a clear self-introduction, explain experience with concrete "
            "examples, answer interview questions, and ask professional follow-up "
            "questions."
        ),
        opening_message=(
            "Hi, thanks for joining today. Could you briefly introduce yourself "
            "and tell me why you are interested in this role?"
        ),
        conversation_style=(
            "Professional, supportive, realistic for an interview, and focused "
            "on one question at a time."
        ),
        feedback_focus=[
            "tense consistency",
            "subject-verb agreement",
            "article usage",
            "professional wording",
            "structured answers",
        ],
        useful_expressions=[
            "I contributed to...",
            "One challenge I faced was...",
            "I am interested in this role because...",
        ],
        scoring_focus=[
            "correct use of past tense, articles, prepositions, and complete sentences",
            "professional tone, natural self-introduction, and polite answers",
            "answer organization, smooth transitions, and ability to expand beyond one sentence",
            "introduces background, explains experience, answers questions, and asks a relevant question",
        ],
    ),
    "ordering_food": ScenarioPromptConfig(
        scenario_id="ordering_food",
        title_zh="点餐",
        title_en="Ordering Food",
        level="Beginner to intermediate",
        ai_role="Restaurant server",
        user_role="Customer",
        goal=(
            "Order food and drinks clearly, ask for recommendations, express "
            "preferences politely, and confirm the order."
        ),
        opening_message="Welcome! Are you ready to order, or would you like a few recommendations first?",
        conversation_style=(
            "Friendly, practical, patient, and focused on completing a restaurant "
            "or cafe order with short natural phrases."
        ),
        feedback_focus=[
            "countable nouns",
            "articles",
            "modal verbs",
            "polite question forms",
            "natural ordering phrases",
        ],
        useful_expressions=[
            "I'd like",
            "Could I have...",
            "Does this come with...",
            "Could we have the bill, please?",
        ],
        scoring_focus=[
            "correct question forms, articles, plural nouns, and simple sentence structure",
            "polite ordering language, natural requests, and clear preference wording",
            "complete order flow and understandable short responses",
            "orders an item, states a preference, asks or answers a menu question, and confirms the order",
        ],
    ),
    "meeting": ScenarioPromptConfig(
        scenario_id="meeting",
        title_zh="会议",
        title_en="Meeting",
        level="Intermediate to advanced",
        ai_role="Team lead",
        user_role="Team member",
        goal=(
            "Give a clear progress update, explain blockers, ask for clarification, "
            "agree on action items, and confirm next steps."
        ),
        opening_message="Let's start with your update. What progress have you made since our last meeting?",
        conversation_style=(
            "Work-focused, concise, collaborative, solution-oriented, and realistic "
            "for a workplace meeting."
        ),
        feedback_focus=[
            "present perfect",
            "past tense",
            "future plans",
            "prepositions",
            "professional update phrases",
            "clear requests",
        ],
        useful_expressions=[
            "The main blocker is...",
            "Could you clarify...",
            "I'll follow up by...",
        ],
        scoring_focus=[
            "accurate tense use, complete sentences, and correct verb patterns",
            "clear workplace phrasing, concise updates, and collaborative tone",
            "progress, blocker, and next-step structure",
            "provides progress, identifies a blocker, asks or answers clarification, and confirms next steps",
        ],
    ),
    "travel": ScenarioPromptConfig(
        scenario_id="travel",
        title_zh="旅行",
        title_en="Travel",
        level="Beginner to intermediate",
        ai_role="Travel service representative or helpful local guide",
        user_role="Traveler",
        goal=(
            "Ask for directions or travel information, check in or confirm a "
            "reservation, explain simple travel problems, and ask for help politely."
        ),
        opening_message="Hello! How can I help you with your trip today?",
        conversation_style=(
            "Clear, patient, and practical, with realistic travel vocabulary and "
            "one travel task at a time."
        ),
        feedback_focus=[
            "question forms",
            "prepositions of place and time",
            "polite modal verbs",
            "travel vocabulary",
            "clear problem descriptions",
        ],
        useful_expressions=[
            "I have a reservation...",
            "Could you tell me how to get to...",
            "Is it possible to...?",
        ],
        scoring_focus=[
            "correct question structure, articles, and prepositions",
            "polite requests, accurate travel terms, and clear explanation of needs",
            "understandable details and smooth responses to service questions",
            "states the travel need, provides required information, asks a useful question, and confirms the result",
        ],
    ),
    "daily_conversation": ScenarioPromptConfig(
        scenario_id="daily_conversation",
        title_zh="日常交流",
        title_en="Daily Conversation",
        level="Beginner to intermediate",
        ai_role="Friendly conversation partner",
        user_role="English learner having a casual conversation",
        goal=(
            "Build comfort with casual English conversation, describe daily life, "
            "share preferences, and ask simple follow-up questions."
        ),
        opening_message="Hi! How's your day going so far?",
        conversation_style=(
            "Casual, friendly, low-pressure, and focused on familiar safe topics."
        ),
        feedback_focus=[
            "basic sentence structure",
            "tense use",
            "word order",
            "common prepositions",
            "natural small talk",
        ],
        useful_expressions=[
            "I usually...",
            "Recently I've been...",
            "That sounds interesting because...",
        ],
        scoring_focus=[
            "basic tense, articles, and sentence structure",
            "natural everyday phrasing and appropriate casual tone",
            "response completeness, added details, and conversational flow",
            "answers questions, shares everyday information, asks a follow-up, and keeps the conversation going",
        ],
    ),
}


SCENARIO_ALIASES = {
    "restaurant": "ordering_food",
    "restaurant-ordering": "ordering_food",
    "ordering-food": "ordering_food",
    "daily": "daily_conversation",
}


def get_scenario_prompt_config(scenario_id: str) -> ScenarioPromptConfig:
    canonical_id = SCENARIO_ALIASES.get(scenario_id, scenario_id)
    return SCENARIO_PROMPT_CONFIGS.get(canonical_id, SCENARIO_PROMPT_CONFIGS["interview"])


def list_scenario_prompt_configs() -> list[ScenarioPromptConfig]:
    return list(SCENARIO_PROMPT_CONFIGS.values())
