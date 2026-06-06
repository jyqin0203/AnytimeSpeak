from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackScoreBreakdown,
    FeedbackResponse,
    PracticeSession,
    Scenario,
    ScoreBreakdown,
    StartSessionRequest,
    SummaryRequest,
    SummaryResponse,
)
from app.scenario_catalog import get_scenario_prompt_config, list_scenario_prompt_configs


SCENARIOS: dict[str, Scenario] = {}
SESSIONS: dict[str, PracticeSession] = {}


def _build_scenarios() -> dict[str, Scenario]:
    scenarios: dict[str, Scenario] = {}
    for config in list_scenario_prompt_configs():
        scenario = Scenario(
            id="restaurant" if config.scenario_id == "ordering_food" else config.scenario_id,
            scenario_id=config.scenario_id,
            title=config.title_en,
            title_zh=config.title_zh,
            level=config.level,
            ai_role=config.ai_role,
            user_role=config.user_role,
            goal=config.goal,
            story_intro=config.story_intro,
            opening_line=config.opening_message,
            opening_message=config.opening_message,
            conversation_style=config.conversation_style,
            feedback_focus=config.feedback_focus,
            useful_expressions=config.useful_expressions,
        )
        scenarios[scenario.id] = scenario
        scenarios[config.scenario_id] = scenario
    return scenarios


SCENARIOS.update(_build_scenarios())


def list_scenarios() -> list[Scenario]:
    return [
        SCENARIOS["interview"],
        SCENARIOS["restaurant"],
        SCENARIOS["meeting"],
        SCENARIOS["travel"],
        SCENARIOS["daily_conversation"],
    ]


def start_session(request: StartSessionRequest) -> PracticeSession:
    scenario = _scenario_for(request.scenario_id)
    session = PracticeSession(
        session_id=f"session_{uuid4().hex[:12]}",
        scenario_id=scenario.id,
        scenario=scenario,
        story_intro=scenario.story_intro,
        opening_message=scenario.opening_message,
        messages=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    SESSIONS[session.session_id] = session
    return session


def create_chat_reply(request: ChatRequest) -> ChatResponse:
    scenario = _scenario_for(request.scenario_id)
    user_message = _latest_user_text(request)
    reply_text = _scenario_reply(scenario.id, user_message)
    feedback = create_feedback(
        FeedbackRequest(
            session_id=request.session_id,
            scenario_id=scenario.id,
            latest_user_message=user_message or "Hello.",
            conversation_history=_conversation_history(request),
        )
    )

    return ChatResponse(
        session_id=request.session_id or f"session_{uuid4().hex[:12]}",
        scenario_id=scenario.id,
        reply=ChatMessage(role="assistant", content=reply_text),
        quick_feedback=feedback,
    )


def create_feedback(request: FeedbackRequest) -> FeedbackResponse:
    scenario = _scenario_for(request.scenario_id)
    message = _feedback_latest_text(request)
    lowered = message.lower()

    if _contains_chinese(message):
        intent = _mixed_language_intent(message)
        expression = _mixed_language_expression(scenario.id, message)
        return _feedback_response(
            what_you_said=message,
            user_intent=intent,
            recommended_english=expression,
            issue=(
                "你可以先用中文或中英夹杂表达想法，意思已经可以理解。"
                "下一步是把核心动作和名词换成自然英文。"
            ),
            why=_code_switching_tip(message, expression),
            more_natural_option=expression,
            score=80,
        )

    if "am graduated" in lowered or "responsible for make" in lowered:
        corrected = (
            message.replace("I am graduated", "I graduated")
            .replace("i am graduated", "I graduated")
            .replace("responsible for make", "responsible for making")
        )
        return _feedback_response(
            what_you_said=message,
            user_intent="The learner is describing past education or project responsibility.",
            recommended_english=corrected,
            issue=(
                "Use the simple past for completed events, and use a gerund after "
                "'responsible for'."
            ),
            why="Completed past events use simple past, and 'for' is followed by a noun or gerund.",
            more_natural_option=(
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
        return _feedback_response(
            what_you_said=message,
            user_intent="The learner wants to order food and ask for a drink recommendation.",
            recommended_english=corrected,
            issue="Use polite request forms and natural restaurant wording.",
            why="'I'd like' and 'Could you...' sound more polite in a restaurant.",
            more_natural_option="I'd like a chicken sandwich, please. Could you recommend a drink for me?",
            score=82,
        )

    if "some problem with api" in lowered or "team give me" in lowered:
        corrected = (
            message.replace("some problem with API", "a problem with the API")
            .replace("backend team give me", "the backend team to give me")
        )
        return _feedback_response(
            what_you_said=message,
            user_intent="The learner is reporting an API blocker and asking the backend team for a format.",
            recommended_english=corrected,
            issue="Use articles with countable nouns and the pattern 'need someone to do something'.",
            why="'A problem with the API' and 'need the team to...' are the natural patterns.",
            more_natural_option=(
                "The main blocker is that I need the backend team to confirm the "
                "API response format."
            ),
            score=76,
        )

    return _feedback_response(
        what_you_said=message,
        user_intent="The learner is continuing the scenario conversation.",
        recommended_english=message,
        issue=f"No major grammar issue for the {scenario.title.lower()} scenario.",
        why="The sentence is understandable and fits the current practice turn.",
        more_natural_option=_default_better_expression(scenario.id),
        score=88,
    )


def create_summary(request: SummaryRequest) -> SummaryResponse:
    scenario = _scenario_for(request.scenario_id)
    history = _summary_history(request)
    user_turns = [message.content for message in history if message.role == "user"]
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
        code_switching_advice=_summary_code_switching_advice(history),
        scores=ScoreBreakdown(
            grammar=grammar,
            expression=expression,
            fluency=fluency,
            scenario_completion=scenario_completion,
            overall=overall,
        ),
    )


def _scenario_for(scenario_id: str) -> Scenario:
    if scenario_id == "restaurant-ordering":
        scenario_id = "restaurant"
    return SCENARIOS.get(scenario_id, SCENARIOS["interview"])


def _conversation_history(request: ChatRequest) -> list[ChatMessage]:
    return request.conversation_history or request.messages


def _summary_history(request: SummaryRequest) -> list[ChatMessage]:
    return request.conversation_history or request.messages


def _latest_user_text(request: ChatRequest) -> str:
    if request.latest_user_message:
        return request.latest_user_message.strip()
    for message in reversed(_conversation_history(request)):
        if message.role == "user":
            return message.content
    return ""


def _feedback_latest_text(request: FeedbackRequest) -> str:
    return (request.latest_user_message or request.message or "").strip()


def _feedback_response(
    *,
    what_you_said: str,
    user_intent: str,
    recommended_english: str,
    issue: str,
    why: str,
    more_natural_option: str,
    score: int,
    provider: str = "mock",
) -> FeedbackResponse:
    score_breakdown = FeedbackScoreBreakdown(
        grammar=max(0, min(100, score - 2)),
        expression=score,
        fluency=max(0, min(100, score + 2)),
        scenario_fit=max(0, min(100, score + 4)),
    )
    return FeedbackResponse(
        what_you_said=what_you_said,
        user_intent=user_intent,
        recommended_english=recommended_english,
        issue=issue,
        why=why,
        more_natural_option=more_natural_option,
        score=score,
        score_breakdown=score_breakdown,
        provider=provider,
        corrected_sentence=recommended_english,
        better_expression=more_natural_option,
        user_intent_zh=user_intent if _contains_chinese(user_intent) else None,
        code_switching_tip=why if _contains_chinese(what_you_said) else None,
    )


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
        if "预约" in user_message or "schedule" in lowered or "meeting tomorrow" in lowered:
            return (
                "That sounds like a scheduling topic. What time works best for the "
                "meeting tomorrow, and who needs to join?"
            )
        if "api" in lowered or "blocker" in lowered:
            return (
                "Thanks for the update. It sounds like the API format is blocking you. "
                "What specific data fields do you need from the backend team?"
            )
        return "Thanks for the update. What is your main blocker or next step for this week?"

    if scenario_id == "travel":
        if "check in" in lowered or "booking" in lowered or "reservation" in lowered:
            return (
                "Let me check that for you. Could I have your name and a sample booking "
                "number, please?"
            )
        return "Sure, I can help with that. What destination or travel detail do you need?"

    if scenario_id == "daily_conversation":
        if "movie" in lowered:
            return "That sounds relaxing. What movie did you watch, and did you enjoy it?"
        return "That sounds good. Could you tell me a little more about your day?"

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
        "ordering_food": "I'd like to order this without onions, please.",
        "meeting": "The main blocker is the API response format.",
        "travel": "I have a reservation here, but I arrived early. Is early check-in available?",
        "daily_conversation": "After work, I relaxed at home and watched a movie.",
    }
    return expressions.get(scenario_id, expressions["interview"])


def _scenario_completion_score(scenario_id: str, text: str, turn_count: int) -> int:
    score = 70 + min(turn_count, 3) * 5
    keywords = {
        "interview": ["experience", "project", "interested", "role"],
        "restaurant": ["order", "sandwich", "drink", "please"],
        "ordering_food": ["order", "sandwich", "drink", "please"],
        "meeting": ["finished", "blocker", "api", "next"],
        "travel": ["reservation", "booking", "direction", "help"],
        "daily_conversation": ["day", "work", "movie", "usually"],
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
        "ordering_food": [
            "Use polite forms such as 'I'd like' and 'Could I have'.",
            "Check articles and singular or plural nouns when ordering.",
        ],
        "meeting": [
            "Use articles with workplace nouns such as 'the API'.",
            "Use 'need someone to do something' for requests.",
        ],
        "travel": [
            "Use polite travel requests such as 'Could you tell me...'.",
            "Check articles and prepositions in travel phrases.",
        ],
        "daily_conversation": [
            "Use past tense for completed daily activities.",
            "Add articles before singular countable nouns such as 'a movie'.",
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
        "ordering_food": [
            "I'd like...",
            "Could I have...",
            "Does this come with...",
        ],
        "meeting": [
            "The main blocker is that I need the backend team to confirm the API response format.",
            "Could you clarify the expected fields?",
            "I'll follow up by the end of today.",
        ],
        "travel": [
            "I have a reservation...",
            "Could you tell me how to get to...",
            "Is it possible to...?",
        ],
        "daily_conversation": [
            "I usually...",
            "Recently I've been...",
            "That sounds interesting because...",
        ],
    }
    return expressions.get(scenario_id, expressions["interview"])


def _next_focus(scenario_id: str) -> str:
    focuses = {
        "interview": "Practice answering with one concrete example and one measurable result.",
        "restaurant": "Practice polite ordering phrases and confirming details.",
        "meeting": "Practice a progress, blocker, and next-step update structure.",
        "ordering_food": "Practice polite ordering phrases and confirming details.",
        "travel": "Practice polite travel requests and confirming key details.",
        "daily_conversation": "Practice adding one detail and one follow-up question in casual English.",
    }
    return focuses.get(scenario_id, focuses["interview"])


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)


def _mixed_language_intent(message: str) -> str:
    if _mentions_scheduling_meeting(message):
        return "我想约一个明天的会议。"
    return message


def _mixed_language_expression(scenario_id: str, message: str) -> str:
    if _mentions_scheduling_meeting(message):
        return "I want to schedule a meeting for tomorrow."
    if scenario_id in {"restaurant", "ordering_food"}:
        return "I'd like to order this, please."
    if scenario_id == "travel":
        return "I need help with my travel plans."
    if scenario_id == "daily_conversation":
        return "After work, I relaxed at home and watched a movie."
    return get_scenario_prompt_config(scenario_id).useful_expressions[0]


def _code_switching_tip(message: str, expression: str) -> str:
    if _mentions_scheduling_meeting(message):
        return f"把“预约一个 meeting”整体换成自然英文：{expression}"
    return f"先保留你的意思，再把中文部分换成完整英文：{expression}"


def _summary_code_switching_advice(messages: list[ChatMessage]) -> str | None:
    mixed_turns = [message for message in messages if message.role == "user" and _contains_chinese(message.content)]
    if not mixed_turns:
        return None
    return (
        "你已经能把想法说出来。下次可以先抓住中文里的核心动作，"
        "例如“预约”对应 schedule，然后组合成完整英文句子。"
    )


def _mentions_scheduling_meeting(message: str) -> bool:
    lowered = message.lower()
    has_schedule_word = "预约" in message or "约" in message or "schedule" in lowered
    has_meeting_word = "meeting" in lowered or "会议" in message
    return has_schedule_word and has_meeting_word
