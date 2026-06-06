from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    Scenario,
    ScoreBreakdown,
    SummaryRequest,
    SummaryResponse,
)


SCENARIOS: dict[str, Scenario] = {
    "interview": Scenario(
        id="interview",
        title="Interview",
        title_zh="面试",
        level="Intermediate",
        ai_role="Hiring manager",
        user_role="Job candidate",
        goal=(
            "Answer interview questions clearly, explain experience, and ask "
            "professional follow-up questions."
        ),
        opening_line=(
            "Hi, thanks for joining today. Could you briefly introduce yourself "
            "and tell me why you are interested in this role?"
        ),
        conversation_style="Professional, warm, and focused on one question at a time.",
        feedback_focus=[
            "tense consistency",
            "professional wording",
            "clear examples",
            "structured answers",
        ],
    ),
    "restaurant": Scenario(
        id="restaurant",
        title="Ordering Food",
        title_zh="点餐",
        level="Beginner to intermediate",
        ai_role="Restaurant server",
        user_role="Customer",
        goal=(
            "Order food, ask about recommendations, clarify preferences, and "
            "handle simple service questions."
        ),
        opening_line="Welcome! Are you ready to order, or would you like a few recommendations first?",
        conversation_style="Friendly, practical, and focused on completing the order.",
        feedback_focus=[
            "polite requests",
            "articles",
            "countable nouns",
            "clear preferences",
        ],
    ),
    "meeting": Scenario(
        id="meeting",
        title="Meeting",
        title_zh="会议",
        level="Intermediate",
        ai_role="Team lead",
        user_role="Team member",
        goal=(
            "Share progress, discuss blockers, ask for clarification, and agree "
            "on next steps."
        ),
        opening_line="Let's start with your update. What progress have you made since our last meeting?",
        conversation_style="Work-focused, concise, collaborative, and action-oriented.",
        feedback_focus=[
            "present perfect",
            "blocker phrasing",
            "clarifying questions",
            "next steps",
        ],
    ),
}


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


def create_chat_reply(request: ChatRequest) -> ChatResponse:
    scenario = _scenario_for(request.scenario_id)
    user_message = _latest_user_text(request.messages)
    reply_text = _scenario_reply(scenario.id, user_message)
    feedback = create_feedback(
        FeedbackRequest(scenario_id=scenario.id, message=user_message or "Hello.")
    )

    return ChatResponse(
        scenario_id=scenario.id,
        reply=ChatMessage(role="assistant", content=reply_text),
        quick_feedback=feedback,
    )


def create_feedback(request: FeedbackRequest) -> FeedbackResponse:
    scenario = _scenario_for(request.scenario_id)
    message = request.message.strip()
    lowered = message.lower()

    if "am graduated" in lowered or "responsible for make" in lowered:
        corrected = (
            message.replace("I am graduated", "I graduated")
            .replace("i am graduated", "I graduated")
            .replace("responsible for make", "responsible for making")
        )
        return FeedbackResponse(
            corrected_sentence=corrected,
            issue=(
                "Use the simple past for completed events, and use a gerund after "
                "'responsible for'."
            ),
            better_expression=(
                "I contributed to a customer research project and prepared the "
                "final report for our team."
            ),
            score=74,
        )

    if "recommend me" in lowered or "i want " in lowered:
        corrected = (
            message.replace("Can you recommend me some drink?", "Could you recommend a drink for me?")
            .replace("I want", "I'd like")
        )
        return FeedbackResponse(
            corrected_sentence=corrected,
            issue="Use polite request forms and natural restaurant wording.",
            better_expression="I'd like a chicken sandwich, please. Could you recommend a drink for me?",
            score=82,
        )

    if "some problem with api" in lowered or "team give me" in lowered:
        corrected = (
            message.replace("some problem with API", "a problem with the API")
            .replace("backend team give me", "the backend team to give me")
        )
        return FeedbackResponse(
            corrected_sentence=corrected,
            issue="Use articles with countable nouns and the pattern 'need someone to do something'.",
            better_expression=(
                "The main blocker is that I need the backend team to confirm the "
                "API response format."
            ),
            score=76,
        )

    return FeedbackResponse(
        corrected_sentence=message,
        issue=f"No major grammar issue for the {scenario.title.lower()} scenario.",
        better_expression=_default_better_expression(scenario.id),
        score=88,
    )


def create_summary(request: SummaryRequest) -> SummaryResponse:
    scenario = _scenario_for(request.scenario_id)
    user_turns = [message.content for message in request.messages if message.role == "user"]
    joined_user_text = " ".join(user_turns).lower()
    turn_count = len(user_turns)

    grammar = 84
    expression = 82
    if any(phrase in joined_user_text for phrase in ["am graduated", "some problem", "team give me"]):
        grammar -= 10
        expression -= 6

    fluency = min(90, 68 + turn_count * 8)
    scenario_completion = _scenario_completion_score(scenario.id, joined_user_text, turn_count)
    overall = round(
        grammar * 0.25
        + expression * 0.25
        + fluency * 0.20
        + scenario_completion * 0.30
    )

    return SummaryResponse(
        scenario_id=scenario.id,
        summary=(
            f"You completed a {scenario.title.lower()} practice session with clear intent "
            "and enough context for the AI role to keep the conversation moving."
        ),
        strengths=[
            "You responded to the scenario prompt with relevant information.",
            "Your meaning was understandable across the conversation.",
        ],
        repeated_issues=_repeated_issues(scenario.id),
        better_expressions=_summary_expressions(scenario.id),
        scenario_completion=(
            f"You practiced the main {scenario.title.lower()} communication goal. "
            "Add one more specific detail or follow-up question next time."
        ),
        next_practice_focus=_next_focus(scenario.id),
        scores=ScoreBreakdown(
            grammar=grammar,
            expression=expression,
            fluency=fluency,
            scenario_completion=scenario_completion,
            overall=overall,
        ),
    )


def _scenario_for(scenario_id: str) -> Scenario:
    return SCENARIOS.get(scenario_id, SCENARIOS["interview"])


def _latest_user_text(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _scenario_reply(scenario_id: str, user_message: str) -> str:
    lowered = user_message.lower()

    if scenario_id == "restaurant":
        if "chicken sandwich" in lowered:
            return (
                "Of course. I can make the chicken sandwich without onions. "
                "For a drink, I recommend iced tea or lemonade. Would you like either of those?"
            )
        return (
            "Sure. Would you like that for here or to go, and would you like a drink "
            "with your order?"
        )

    if scenario_id == "meeting":
        if "api" in lowered or "blocker" in lowered:
            return (
                "Thanks for the update. It sounds like the API format is blocking you. "
                "What specific data fields do you need from the backend team?"
            )
        return "Thanks for the update. What is your main blocker or next step for this week?"

    if "project" in lowered or "experience" in lowered:
        return (
            "Thanks for sharing that. Could you tell me one concrete example of your "
            "work and how it helped the team make a decision?"
        )
    return (
        "Thanks for the introduction. Could you share one relevant project or experience "
        "that shows why you are a good fit for this role?"
    )


def _default_better_expression(scenario_id: str) -> str:
    expressions = {
        "interview": "I contributed to this project by preparing the final report.",
        "restaurant": "I'd like to order this without onions, please.",
        "meeting": "The main blocker is the API response format.",
    }
    return expressions.get(scenario_id, expressions["interview"])


def _scenario_completion_score(scenario_id: str, text: str, turn_count: int) -> int:
    score = 70 + min(turn_count, 3) * 5
    keywords = {
        "interview": ["experience", "project", "interested", "role"],
        "restaurant": ["order", "sandwich", "drink", "please"],
        "meeting": ["finished", "blocker", "api", "next"],
    }
    score += sum(4 for keyword in keywords.get(scenario_id, []) if keyword in text)
    return min(score, 95)


def _repeated_issues(scenario_id: str) -> list[str]:
    issues = {
        "interview": [
            "Watch tense consistency when describing past experience.",
            "Use gerunds after prepositions such as 'responsible for'.",
        ],
        "restaurant": [
            "Use polite forms such as 'I'd like' and 'Could I have'.",
            "Check articles and singular or plural nouns when ordering.",
        ],
        "meeting": [
            "Use articles with workplace nouns such as 'the API'.",
            "Use 'need someone to do something' for requests.",
        ],
    }
    return issues.get(scenario_id, issues["interview"])


def _summary_expressions(scenario_id: str) -> list[str]:
    expressions = {
        "interview": [
            "I contributed to...",
            "One challenge I faced was...",
            "I am interested in this role because...",
        ],
        "restaurant": [
            "I'd like...",
            "Could I have...",
            "Does this come with...",
        ],
        "meeting": [
            "The main blocker is that I need the backend team to confirm the API response format.",
            "Could you clarify the expected fields?",
            "I'll follow up by the end of today.",
        ],
    }
    return expressions.get(scenario_id, expressions["interview"])


def _next_focus(scenario_id: str) -> str:
    focuses = {
        "interview": "Practice answering with one concrete example and one measurable result.",
        "restaurant": "Practice polite ordering phrases and confirming details.",
        "meeting": "Practice a progress, blocker, and next-step update structure.",
    }
    return focuses.get(scenario_id, focuses["interview"])
