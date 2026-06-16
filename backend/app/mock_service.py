import random
import re
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
from app.scenario_catalog import (
    ScenarioPromptConfig,
    StorySeed,
    get_scenario_prompt_config,
    list_scenario_prompt_configs,
)


SCENARIOS: dict[str, Scenario] = {}
SESSIONS: dict[str, PracticeSession] = {}


def _build_scenarios() -> dict[str, Scenario]:
    scenarios: dict[str, Scenario] = {}
    for config in list_scenario_prompt_configs():
        seed = config.default_story_seed
        scenario = Scenario(
            id="restaurant" if config.scenario_id == "ordering_food" else config.scenario_id,
            scenario_id=config.scenario_id,
            title=config.title_en,
            title_zh=config.title_zh,
            level=config.level,
            ai_role=config.ai_role,
            user_role=config.user_role,
            goal=config.goal,
            story_seed_id=seed.seed_id,
            story_intro_zh=seed.story_intro_zh,
            story_intro_en=seed.story_intro_en,
            opening_line=seed.opening_message,
            opening_message=seed.opening_message,
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


def get_session(session_id: str | None) -> PracticeSession | None:
    if not session_id:
        return None
    return SESSIONS.get(session_id)


def _select_story_seed(config: ScenarioPromptConfig, requested_seed_id: str | None) -> StorySeed:
    if requested_seed_id:
        for seed in config.story_seeds:
            if seed.seed_id == requested_seed_id:
                return seed
    return random.choice(config.story_seeds)


def start_session(request: StartSessionRequest) -> PracticeSession:
    scenario_id = _canonical_scenario_id(request.scenario_id)
    config = get_scenario_prompt_config(scenario_id)
    seed = _select_story_seed(config, request.story_seed_id)
    base_scenario = _scenario_for(scenario_id)

    scenario = base_scenario.model_copy(
        update={
            "story_seed_id": seed.seed_id,
            "story_intro_zh": seed.story_intro_zh,
            "story_intro_en": seed.story_intro_en,
            "opening_line": seed.opening_message,
            "opening_message": seed.opening_message,
        }
    )

    session = PracticeSession(
        session_id=f"session_{uuid4().hex[:12]}",
        scenario_id=scenario.id,
        scenario=scenario,
        story_seed_id=seed.seed_id,
        story_intro_zh=seed.story_intro_zh,
        story_intro_en=seed.story_intro_en,
        opening_message=seed.opening_message,
        messages=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    SESSIONS[session.session_id] = session
    return session


def resolve_scenario(session_id: str | None, scenario_id: str) -> Scenario:
    session = get_session(session_id)
    if session is not None:
        return session.scenario
    return _scenario_for(scenario_id)


def create_chat_reply(request: ChatRequest) -> ChatResponse:
    scenario = resolve_scenario(request.session_id, request.scenario_id)
    user_message = _latest_user_text(request)
    reply_text = _scenario_reply(scenario.id, user_message, _conversation_history(request))

    return ChatResponse(
        session_id=request.session_id or f"session_{uuid4().hex[:12]}",
        scenario_id=scenario.id,
        reply=ChatMessage(role="assistant", content=reply_text),
        provider="mock",
    )


def create_feedback(request: FeedbackRequest) -> FeedbackResponse:
    scenario = resolve_scenario(request.session_id, request.scenario_id)
    message = _feedback_latest_text(request) or "Hello."

    has_chinese = _contains_chinese(message)
    word_count = len(message.split())
    on_topic = _is_on_topic(scenario, message)
    chinglish_hits = _detect_chinglish(message)
    grammar_hits = _detect_grammar_issues(message)
    incomplete_hits = _detect_incomplete_expression(message)

    grammar = 90
    naturalness = 90
    relevance = 90 if on_topic else 66
    clarity = 90

    issue_notes: list[str] = []
    why_notes: list[str] = []

    if _detect_daily_plan_invitation(message):
        naturalness -= 10
        clarity -= 8
        issue_notes.append("你的意思能理解，可以把几个动作按更清楚的顺序整理成自然的邀请。")
        why_notes.append(
            "几个动作连在一起时，英语里通常会按“时间 → 计划 → 邀请”的顺序表达。"
            "先说 after lunch，再说 I’m planning to do my homework，最后用 Do you want to join me? 发出邀请，会更自然也更容易理解。"
        )

    if has_chinese:
        naturalness -= 14
        clarity -= 8
        issue_notes.append("你的意思表达清楚了，可以把其中的关键词换成更自然的英文口语说法。")
        why_notes.append(_mixed_input_why(message))

    if grammar_hits:
        pattern, fix = grammar_hits[0]
        grammar -= 12
        clarity -= 4
        issue_notes.append(f"注意 “{pattern}” 这里的用法，更地道的说法是 “{fix}”。")
        why_notes.append("时态、单复数和介词搭配是口语里最容易被听出来的细节，调整后会显得更专业、更自然。")

    if incomplete_hits:
        pattern, fix = incomplete_hits[0]
        grammar -= 10
        clarity -= 12
        issue_notes.append(f"“{pattern}” 还缺少结尾信息，可以补成 “{fix}”。")
        why_notes.append("你的意思能看出来是在询问饮品，但句子停在 with 后面会让对方等后续内容。补上 that 或直接改成完整问句，听起来更自然。")

    if "what do you do recently" in message.lower():
        naturalness -= 8
        issue_notes.append("“What do you do recently?” 不自然。询问近况通常用现在完成时，而不是一般现在时的 “do recently”。")
        why_notes.append("日常交流里更自然的问法是 “What have you been up to recently?” 或 “What have you been doing recently?”。")

    if chinglish_hits:
        pattern, fix = chinglish_hits[0]
        naturalness -= 10
        issue_notes.append(f"“{pattern}” 这种说法偏中式英语，母语者更习惯说 “{fix}”。")
        why_notes.append(f"换成 “{fix}” 这样的地道搭配，会更符合母语者的表达习惯，听起来也更顺耳。")

    if not on_topic:
        relevance -= 18
        issue_notes.append(f"这句话和当前“{scenario.title_zh}”场景的目标关联较弱，可以再贴近一下情境。")
        why_notes.append(f"紧扣 {scenario.ai_role} 关心的内容来组织表达，对话会更顺畅地推进到下一步。")

    if word_count <= 3:
        clarity -= 10
        naturalness -= 4
        issue_notes.append("这句话信息量比较少，建议补充一两个具体细节，让对方更容易接住话题。")
        why_notes.append("加入具体的人物、时间、原因或例子，可以让表达更完整，也更容易引出下一轮对话。")

    if not issue_notes:
        issue_notes.append("这句话整体清楚、语法也没有明显问题，已经达到了这一轮的表达目标。")
        why_notes.append("可以尝试加入一个自然的连接词或具体细节，让口语听起来更像母语者的延伸表达，而不只是正确。")

    issue = " ".join(issue_notes[:2])
    why = " ".join(why_notes[:2])

    recommended_english = _compose_recommended_english(
        scenario,
        message,
        has_chinese,
        grammar_hits,
        chinglish_hits,
        incomplete_hits,
    )
    more_natural_option = _compose_more_natural_option(scenario, recommended_english)
    user_intent = _describe_user_intent(scenario, message, has_chinese)

    return _feedback_response(
        what_you_said=message,
        user_intent=user_intent,
        recommended_english=recommended_english,
        issue=issue,
        why=why,
        more_natural_option=more_natural_option,
        grammar=grammar,
        naturalness=naturalness,
        relevance=relevance,
        clarity=clarity,
    )


def create_summary(request: SummaryRequest) -> SummaryResponse:
    scenario = resolve_scenario(request.session_id, request.scenario_id)
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
            f"你完成了一次「{scenario.title_zh}」场景的练习，目标表达得比较清楚，"
            "也给了 AI 角色足够的信息来推进这段对话。"
        ),
        strengths=[
            "你的回答围绕场景目标展开，信息相关且有内容。",
            "整体表达可以被理解，对话能够顺利进行下去。",
        ],
        repeated_issues=_repeated_issues(scenario.id),
        better_expressions=_summary_expressions(scenario.id),
        scenario_completion=(
            f"你已经完成了「{scenario.title_zh}」场景的主要沟通目标。"
            "下次可以再补充一个具体细节或追问，让回答更完整。"
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
        provider="mock",
    )


def _scenario_for(scenario_id: str) -> Scenario:
    scenario_id = _canonical_scenario_id(scenario_id)
    if scenario_id == "restaurant-ordering":
        scenario_id = "restaurant"
    return SCENARIOS.get(scenario_id, SCENARIOS["interview"])


def _canonical_scenario_id(scenario_id: str) -> str:
    aliases = {
        "daily": "daily_conversation",
        "restaurant-ordering": "restaurant",
        "ordering_food": "restaurant",
    }
    return aliases.get(scenario_id, scenario_id)


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
    grammar: int,
    naturalness: int,
    relevance: int,
    clarity: int,
    provider: str = "mock",
) -> FeedbackResponse:
    score_breakdown = FeedbackScoreBreakdown(
        grammar=_clamp_score(grammar),
        naturalness=_clamp_score(naturalness),
        relevance=_clamp_score(relevance),
        clarity=_clamp_score(clarity),
    )
    return FeedbackResponse(
        what_you_said=what_you_said,
        user_intent=user_intent,
        recommended_english=recommended_english,
        issue=issue,
        why=why,
        more_natural_option=more_natural_option,
        score=_overall_score(score_breakdown),
        score_breakdown=score_breakdown,
        provider=provider,
        corrected_sentence=recommended_english,
        better_expression=more_natural_option,
        user_intent_zh=user_intent if _contains_chinese(user_intent) else None,
        code_switching_tip=why if _contains_chinese(what_you_said) else None,
    )


def _clamp_score(value: int) -> int:
    return max(35, min(98, value))


def _overall_score(breakdown: FeedbackScoreBreakdown) -> int:
    weighted = (
        breakdown.grammar * 0.25
        + breakdown.naturalness * 0.30
        + breakdown.relevance * 0.25
        + breakdown.clarity * 0.20
    )
    return round(weighted)


def _scenario_reply(
    scenario_id: str,
    user_message: str,
    history: list[ChatMessage] | None = None,
) -> str:
    lowered = user_message.lower()

    if _detect_negative_emotion(user_message):
        return _negative_emotion_reply(scenario_id)

    if scenario_id == "restaurant":
        if "chicken sandwich" in lowered:
            return _avoid_repeated_reply(
                (
                    "Of course. I can make the chicken sandwich without onions. "
                    "Would you like a drink with that?"
                ),
                history,
                "Sure. Would you like that for here or to go?",
            )
        if _detect_restaurant_preference(user_message):
            return _avoid_repeated_reply(
                "Sure. I can recommend something mild. Would you prefer chicken, beef, or vegetables?",
                history,
                "Got it. Would you like a mild noodle dish or a rice dish?",
            )
        return _avoid_repeated_reply(
            (
                "Sure. Would you like that for here or to go, or would you like a drink "
                "with that?"
            ),
            history,
            "Got it. Would you like anything else with your order?",
        )

    if scenario_id == "meeting":
        if "预约" in user_message or "schedule" in lowered or "meeting tomorrow" in lowered:
            return _avoid_repeated_reply(
                (
                    "That sounds like a scheduling topic. What time works best for the "
                    "meeting tomorrow?"
                ),
                history,
                "Who needs to join that meeting?",
            )
        if "api" in lowered or "blocker" in lowered:
            return _avoid_repeated_reply(
                (
                    "Thanks for the update. It sounds like the API format is blocking you. "
                    "What specific data fields do you need?"
                ),
                history,
                "What support do you need from the backend team?",
            )
        return _avoid_repeated_reply(
            "Thanks for the update. What is your main blocker or next step for this week?",
            history,
            "What support do you need from the team this week?",
        )

    if scenario_id == "travel":
        if "check in" in lowered or "booking" in lowered or "reservation" in lowered:
            return _avoid_repeated_reply(
                (
                    "Let me check that for you. Could I have your name and a sample booking "
                    "number, please?"
                ),
                history,
                "What time did you arrive at the hotel?",
            )
        return _avoid_repeated_reply(
            "Sure, I can help with that. What destination or travel detail do you need?",
            history,
            "What would you like help with first?",
        )

    if scenario_id == "daily_conversation":
        if _detect_daily_plan_invitation(user_message):
            return _avoid_repeated_reply(
                "Sure, that sounds like a plan. What time do you want to go?",
                history,
                "That sounds nice. Are you thinking about lunch first and then homework?",
            )
        if "movie" in lowered:
            return _avoid_repeated_reply(
                "That sounds relaxing. What movie did you watch, and did you enjoy it?",
                history,
                "What kind of movies do you usually like?",
            )
        return _avoid_repeated_reply(
            "I hear you. What has been on your mind today?",
            history,
            "Could you tell me a little more about what happened?",
        )

    if "project" in lowered or "experience" in lowered:
        return _avoid_repeated_reply(
            (
                "Thanks for sharing that project. What challenge did you face, and what result did you achieve?"
            ),
            history,
            "What challenge did you face in that project?",
        )
    return _avoid_repeated_reply(
        (
            "Thanks for the introduction. Could you share one relevant project or experience "
            "that shows why you are a good fit for this role?"
        ),
        history,
        "What kind of role are you most interested in?",
    )


def _avoid_repeated_reply(
    candidate: str,
    history: list[ChatMessage] | None,
    alternative: str,
) -> str:
    last_assistant = _last_assistant_text(history)
    if last_assistant and _normalize_text(last_assistant) == _normalize_text(candidate):
        return alternative
    return candidate


def _last_assistant_text(history: list[ChatMessage] | None) -> str:
    for message in reversed(history or []):
        if message.role == "assistant":
            return message.content
    return ""


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


_NEGATIVE_EMOTION_MARKERS = (
    "伤心",
    "难过",
    "累",
    "疲惫",
    "焦虑",
    "紧张",
    "压力大",
    "sad",
    "upset",
    "down",
    "anxious",
    "tired",
    "stressed",
    "stress",
    "afraid",
    "scared",
    "frustrated",
    "nervous",
)


def _detect_negative_emotion(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered or marker in message for marker in _NEGATIVE_EMOTION_MARKERS)


def _negative_emotion_reply(scenario_id: str) -> str:
    if scenario_id == "interview":
        return "I'm sorry you're feeling that way. What part of the interview prep feels hardest right now?"
    if scenario_id == "meeting":
        return "That sounds really stressful. What is the biggest blocker for you right now?"
    if scenario_id == "travel":
        return "I'm sorry you're dealing with that. What happened, and how can I help with your trip?"
    if scenario_id in {"restaurant", "ordering_food"}:
        return "I'm sorry you're feeling that way. Would you like a moment, or can I help you choose something comforting?"
    return "I'm sorry you're feeling that way. What happened?"


_DAILY_PLAN_INVITATION_MARKERS = (
    "lunch",
    "food",
    "homework",
    "class",
    "go with me",
    "come with me",
    "want to come",
    "join me",
    "delicious",
    "一起",
    "作业",
    "午饭",
    "午餐",
    "吃饭",
)


def _detect_daily_plan_invitation(message: str) -> bool:
    lowered = message.lower()
    has_plan = any(marker in lowered or marker in message for marker in _DAILY_PLAN_INVITATION_MARKERS)
    has_sequence_or_invite = any(
        marker in lowered
        for marker in ("after", "then", "go with me", "come with me", "join me", "do you want")
    )
    return has_plan and has_sequence_or_invite


def _detect_restaurant_preference(message: str) -> bool:
    lowered = message.lower()
    preference_markers = (
        "not too spicy",
        "mild",
        "spicy",
        "recommend",
        "something",
        "preference",
        "dish",
        "allergy",
    )
    return any(marker in lowered for marker in preference_markers)


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
            "描述过去经历时，注意时态前后保持一致。",
            "“responsible for” 后面要接动名词（doing），不要用动词原形。",
        ],
        "restaurant": [
            "可以多用 “I'd like”“Could I have” 这类礼貌表达。",
            "点餐时注意冠词，以及名词的单复数形式。",
        ],
        "ordering_food": [
            "可以多用 “I'd like”“Could I have” 这类礼貌表达。",
            "点餐时注意冠词，以及名词的单复数形式。",
        ],
        "meeting": [
            "“the API” 这类职场名词前别忘了加冠词。",
            "请求支持时可以用 “need someone to do something” 的句型。",
        ],
        "travel": [
            "可以多用 “Could you tell me...” 这类礼貌的旅行用语。",
            "注意旅行常用短语里的冠词和介词搭配。",
        ],
        "daily_conversation": [
            "描述已经完成的日常活动时，要用过去时。",
            "可数名词单数前别忘了加冠词，比如 “a movie”。",
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
        "interview": "练习用“一个具体例子 + 一个可衡量的结果”来回答问题。",
        "restaurant": "练习礼貌的点餐句型，并在最后确认订单细节。",
        "meeting": "练习“进展 → 阻塞点 → 下一步”这样的汇报结构。",
        "ordering_food": "练习礼貌的点餐句型，并在最后确认订单细节。",
        "travel": "练习礼貌的旅行请求句型，并确认关键信息。",
        "daily_conversation": "练习在闲聊里多加一个细节和一个追问，让对话更自然。",
    }
    return focuses.get(scenario_id, focuses["interview"])


def _contains_chinese(text: str) -> bool:
    return any("一" <= character <= "鿿" for character in text)


_GENERIC_OPENER_WORDS = {
    "hi", "hello", "hey", "thanks", "thank", "yes", "no", "ok", "okay", "sure", "sorry",
}
_GENERIC_OPENER_PHRASES_ZH = ("你好", "谢谢", "好的", "是的", "嗯", "哈喽", "抱歉")

_SCENARIO_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "interview": [
        "experience", "project", "role", "team", "intern", "resume", "interview",
        "background", "skill", "challenge", "responsible", "graduated",
        "学习", "项目", "面试", "实习", "经验", "经历",
    ],
    "ordering_food": [
        "order", "menu", "drink", "food", "recommend", "sandwich", "coffee", "takeout",
        "table", "dish", "allerg", "spicy", "mild", "preference", "点", "餐", "推荐", "外卖", "菜", "饮料",
    ],
    "meeting": [
        "progress", "blocker", "update", "task", "deadline", "team", "api", "sync",
        "meeting", "next step", "schedule", "进度", "会议", "阻塞", "汇报", "预约",
    ],
    "travel": [
        "hotel", "check in", "check-in", "check out", "room", "reservation", "direction",
        "station", "airport", "ticket", "luggage", "酒店", "入住", "车站", "机场", "行李", "问路",
    ],
    "daily_conversation": [
        "weekend", "movie", "class", "homework", "plan", "friend", "classmate", "coffee",
        "relax", "recently", "project", "projects", "ai", "lunch", "food", "join", "go with me",
        "周末", "电影", "同学", "计划", "作业",
        "聊天", "最近", "项目", "应用开发",
    ],
}


def _is_on_topic(scenario: Scenario, message: str) -> bool:
    stripped = message.strip()
    if len(stripped) <= 2:
        return True
    if _detect_negative_emotion(stripped):
        return True

    lowered = stripped.lower()
    words = set(re.findall(r"[a-z']+", lowered))
    if words & _GENERIC_OPENER_WORDS:
        return True
    if any(phrase in stripped for phrase in _GENERIC_OPENER_PHRASES_ZH):
        return True

    keywords = _SCENARIO_TOPIC_KEYWORDS.get(scenario.scenario_id, [])
    return any(keyword in lowered for keyword in keywords)


_CHINGLISH_PATTERNS: list[tuple[str, str]] = [
    ("very like", "really like / like ... a lot"),
    ("more better", "better"),
    ("more cheaper", "cheaper"),
    ("open the light", "turn on the light"),
    ("close the light", "turn off the light"),
    ("how to say", "what's the word for / how do you say"),
    ("give you trouble", "cause you any trouble"),
    ("i very", "I'm really / I really"),
    ("discuss about", "discuss"),
    ("less people", "fewer people"),
]


def _detect_chinglish(message: str) -> list[tuple[str, str]]:
    lowered = message.lower()
    return [(pattern, fix) for pattern, fix in _CHINGLISH_PATTERNS if pattern in lowered]


_GRAMMAR_PATTERNS: list[tuple[str, str]] = [
    ("i am graduated", "I graduated"),
    ("what do you do recently", "What have you been up to recently"),
    ("i are", "I am"),
    ("he don't", "he doesn't"),
    ("she don't", "she doesn't"),
    ("responsible for make", "responsible for making"),
    ("recommend me", "recommend ... for me"),
]


def _detect_grammar_issues(message: str) -> list[tuple[str, str]]:
    lowered = message.lower()
    return [(pattern, fix) for pattern, fix in _GRAMMAR_PATTERNS if pattern in lowered]


def _detect_incomplete_expression(message: str) -> list[tuple[str, str]]:
    stripped = message.strip().rstrip(".!?").lower()
    if stripped.endswith("would you like a drink with") or stripped.endswith("like a drink with"):
        return [("would you like a drink with", "Would you like a drink with that?")]
    return []


def _compose_recommended_english(
    scenario: Scenario,
    message: str,
    has_chinese: bool,
    grammar_hits: list[tuple[str, str]],
    chinglish_hits: list[tuple[str, str]],
    incomplete_hits: list[tuple[str, str]] | None = None,
) -> str:
    lowered = message.lower()
    if incomplete_hits:
        return incomplete_hits[0][1]
    if _detect_daily_plan_invitation(message):
        return "Of course! After lunch, I’m planning to do my homework. Do you want to join me?"
    if scenario.id == "restaurant" and _detect_restaurant_preference(message):
        return "I’d like something that isn’t too spicy. What would you recommend?"
    if "what do you do recently" in lowered:
        return "What have you been up to recently?"
    if "recently completed" in lowered and "ai" in lowered and ("项目" in message or "应用开发" in message):
        return "I recently completed two AI application development projects."
    emotion_rewrite = _emotion_recommended_english(message)
    if emotion_rewrite:
        return emotion_rewrite
    if has_chinese:
        return _translate_mixed_message(scenario, message)

    rewritten = message.strip()
    for pattern, fix in grammar_hits + chinglish_hits:
        rewritten = re.sub(re.escape(pattern), fix, rewritten, flags=re.IGNORECASE)

    return _ensure_sentence_punctuation(rewritten)


def _emotion_recommended_english(message: str) -> str | None:
    lowered = message.lower()
    if any(token in message for token in ("伤心", "难过")) or any(token in lowered for token in ("sad", "upset", "down")):
        return "I'm feeling really sad right now."
    if "焦虑" in message or "anxious" in lowered:
        return "I'm feeling really anxious right now."
    if "紧张" in message or "nervous" in lowered:
        return "I'm feeling really nervous right now."
    if "压力大" in message or "stressed" in lowered or "stress" in lowered:
        return "I'm feeling really stressed right now."
    if any(token in message for token in ("累", "疲惫")) or "tired" in lowered:
        return "I'm feeling really tired right now."
    return None


def _mixed_input_why(message: str) -> str:
    if any(token in message for token in ("伤心", "难过")):
        return (
            "你的意思表达清楚了，这里可以把“伤心”换成英文里更常用的情绪词，"
            "比如 sad、upset 或 feeling down。口语里用 “I'm feeling...” "
            "会比 “I am so...” 更自然，也更像在描述自己当下的状态。"
        )
    if "焦虑" in message:
        return (
            "你的意思表达清楚了，这里可以把“焦虑”换成 anxious。口语里用 "
            "“I'm feeling anxious right now” 能更自然地表达当下状态。"
        )
    if "紧张" in message:
        return (
            "你的意思表达清楚了，这里可以把“紧张”换成 nervous。口语里用 "
            "“I'm feeling nervous” 更像自然地描述自己的感受。"
        )
    if "压力大" in message:
        return (
            "你的意思表达清楚了，这里可以把“压力大”换成 stressed。口语里用 "
            "“I've been feeling stressed lately” 能更自然地表达最近的状态。"
        )
    if any(token in message for token in ("累", "疲惫")):
        return (
            "你的意思表达清楚了，这里可以把这个感受换成 tired 或 exhausted。"
            "口语里用 “I'm feeling...” 能更自然地描述当下状态。"
        )
    return (
        "你的意思表达清楚了，可以把中文里的核心词换成对应的英文词或常用搭配。"
        "这样不会改变你的原意，只是让句子听起来更像自然口语。"
    )


def _translate_mixed_message(scenario: Scenario, message: str) -> str:
    if _mentions_scheduling_meeting(message):
        return "I'd like to schedule a meeting for tomorrow, if that works for you."
    if "ai" in message.lower() and ("项目" in message or "应用开发" in message):
        return "I recently completed two AI application development projects."

    fragments = _extract_known_fragments(message)
    stripped = message.strip()
    is_question = stripped.endswith(("?", "？")) or any(
        token in stripped for token in ("吗", "呢", "怎么", "什么", "哪")
    )
    is_request = any(
        token in stripped
        for token in ("我想", "我要", "想要", "麻烦", "可以帮", "帮我", "能不能")
    )

    if fragments:
        topic = ", ".join(fragments[:3])
        if is_question:
            return f"Could you tell me more about {topic}?"
        if is_request:
            return f"I'd like to {topic}, if that's possible."
        return f"I'd like to talk about {topic} in this conversation."

    return _default_better_expression(scenario.scenario_id)


_STOP_WORDS = {
    "i", "a", "an", "the", "to", "is", "am", "are", "of", "in", "on", "and", "for",
    "it", "you", "we", "my", "me", "this", "that", "with", "at", "be",
}

_ZH_EN_VOCAB: list[tuple[str, str]] = [
    ("预约", "schedule"),
    ("安排", "arrange"),
    ("会议", "a meeting"),
    ("明天", "tomorrow"),
    ("今天", "today"),
    ("下周", "next week"),
    ("点餐", "place an order"),
    ("点单", "place an order"),
    ("推荐", "a recommendation"),
    ("菜单", "the menu"),
    ("打包", "to take it to go"),
    ("外卖", "a takeout order"),
    ("入住", "check in"),
    ("退房", "check out"),
    ("房间", "a room"),
    ("预订", "a reservation"),
    ("怎么走", "how to get there"),
    ("地铁站", "the subway station"),
    ("火车站", "the train station"),
    ("机场", "the airport"),
    ("项目", "the project"),
    ("应用开发", "application development"),
    ("经验", "my experience"),
    ("实习", "the internship"),
    ("面试", "the interview"),
    ("挑战", "a challenge"),
    ("阻塞", "a blocker"),
    ("进度", "the progress"),
    ("汇报", "an update"),
    ("同学", "my classmate"),
    ("周末", "the weekend"),
    ("计划", "plans"),
    ("电影", "a movie"),
    ("作业", "homework"),
    ("咖啡", "coffee"),
    ("帮我", "help me"),
]


def _extract_known_fragments(message: str) -> list[str]:
    fragments: list[str] = []
    seen: set[str] = set()

    for match in re.findall(r"[A-Za-z][A-Za-z'\-]*", message):
        lowered = match.lower()
        if lowered in _STOP_WORDS or lowered in seen:
            continue
        seen.add(lowered)
        fragments.append(match)

    for zh, en in _ZH_EN_VOCAB:
        if zh in message and en.lower() not in seen:
            seen.add(en.lower())
            fragments.append(en)

    return fragments


def _compose_more_natural_option(scenario: Scenario, recommended_english: str) -> str:
    if "sad" in recommended_english.lower() or "upset" in recommended_english.lower() or "down" in recommended_english.lower():
        return "I've been feeling really down lately."
    if "after lunch" in recommended_english.lower() and "homework" in recommended_english.lower():
        return "Sure! After lunch, I’m going to do my homework. Do you want to come with me?"
    if scenario.id == "restaurant" and "spicy" in recommended_english.lower():
        return "Could you recommend a mild dish for me?"
    if recommended_english.endswith("?"):
        return recommended_english
    base = recommended_english.rstrip(".!?")
    return f"{base}. {_scenario_connector(scenario.scenario_id)}"


def _scenario_connector(scenario_id: str) -> str:
    connectors = {
        "interview": "I'd be glad to walk you through the details if that's helpful.",
        "ordering_food": "If you have a recommendation, I'm happy to hear it.",
        "meeting": "I can share more specifics if that would help the team.",
        "travel": "Please let me know if you need any more information from me.",
        "daily_conversation": "I'd love to hear what you think about it too.",
    }
    return connectors.get(scenario_id, connectors["interview"])


def _describe_user_intent(scenario: Scenario, message: str, has_chinese: bool) -> str:
    stripped = message.strip()
    if has_chinese:
        return stripped
    snippet = stripped if len(stripped) <= 60 else f"{stripped[:60]}…"
    return f"你正在围绕“{scenario.title_zh}”场景表达：{snippet}"


def _ensure_sentence_punctuation(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


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
