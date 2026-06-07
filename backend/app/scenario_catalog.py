from dataclasses import dataclass, field


@dataclass(frozen=True)
class StorySeed:
    seed_id: str
    label_zh: str
    story_intro_zh: str
    story_intro_en: str
    opening_message: str


@dataclass(frozen=True)
class ScenarioPromptConfig:
    scenario_id: str
    title_zh: str
    title_en: str
    level: str
    ai_role: str
    user_role: str
    goal: str
    conversation_style: str
    feedback_focus: list[str]
    useful_expressions: list[str]
    scoring_focus: list[str]
    story_seeds: list[StorySeed] = field(default_factory=list)

    @property
    def default_story_seed(self) -> StorySeed:
        return self.story_seeds[0]


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
        story_seeds=[
            StorySeed(
                seed_id="interview_first_round",
                label_zh="线上初面",
                story_intro_zh=(
                    "你正在参加一家创业公司的第一轮线上面试。招聘经理刚打开摄像头，"
                    "准备从你的背景和动机开始了解你，整场大约 20 分钟，氛围比较轻松。"
                ),
                story_intro_en=(
                    "You are joining the first-round video interview for a startup. "
                    "The hiring manager has just turned on the camera and wants to "
                    "start with your background and motivation in a relaxed "
                    "twenty-minute conversation."
                ),
                opening_message=(
                    "Hi, thanks for joining today. Could you briefly introduce "
                    "yourself and tell me why you are interested in this role?"
                ),
            ),
            StorySeed(
                seed_id="interview_project_dive",
                label_zh="项目经历追问",
                story_intro_zh=(
                    "面试已经进入第二轮，招聘经理看过你简历上的一个项目，想让你具体讲讲"
                    "你在其中做了什么、遇到了什么挑战，以及最终的结果。"
                ),
                story_intro_en=(
                    "You are now in a second-round interview. The hiring manager has "
                    "read about one project on your resume and wants you to walk "
                    "through your specific role, the challenge you faced, and the "
                    "result."
                ),
                opening_message=(
                    "Thanks for joining the second round. I noticed a project on "
                    "your resume — could you walk me through what you did and what "
                    "the result was?"
                ),
            ),
            StorySeed(
                seed_id="interview_internship",
                label_zh="实习岗位面试",
                story_intro_zh=(
                    "你正在面试一个暑期实习岗位，对方是带教导师。面试官想知道你目前的"
                    "学习方向、能投入的时间，以及你希望从这次实习中获得什么。"
                ),
                story_intro_en=(
                    "You are interviewing for a summer internship with your "
                    "potential mentor. The interviewer wants to know your current "
                    "focus, the time you can commit, and what you hope to gain from "
                    "the internship."
                ),
                opening_message=(
                    "Hi, welcome! Could you tell me a bit about what you are "
                    "currently studying and why this internship caught your "
                    "interest?"
                ),
            ),
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
        story_seeds=[
            StorySeed(
                seed_id="ordering_cafe",
                label_zh="咖啡店点单",
                story_intro_zh=(
                    "上午十点，你走进公司楼下的咖啡店准备点一杯饮品。店员很热情，队伍"
                    "不算长，你可以慢慢说明你想要的口味和分量。"
                ),
                story_intro_en=(
                    "At ten in the morning, you walk into the cafe near your office "
                    "to order a drink. The barista is friendly and the line is "
                    "short, so you can take your time describing your preferred "
                    "flavor and size."
                ),
                opening_message="Good morning! What can I get started for you today?",
            ),
            StorySeed(
                seed_id="ordering_restaurant_recommend",
                label_zh="餐厅询问推荐",
                story_intro_zh=(
                    "你和朋友来到一家没吃过的餐厅，菜单上的选项有点多，你决定向服务员"
                    "询问推荐，再根据口味做出选择。"
                ),
                story_intro_en=(
                    "You and a friend arrive at a restaurant you have never tried "
                    "before. The menu has many options, so you decide to ask the "
                    "server for recommendations before deciding what to order."
                ),
                opening_message="Welcome! Are you ready to order, or would you like a few recommendations first?",
            ),
            StorySeed(
                seed_id="ordering_takeout",
                label_zh="外卖 / 打包场景",
                story_intro_zh=(
                    "你赶时间，打算点一份外卖带走。你需要快速说明想要什么、有什么忌口，"
                    "并确认打包和等待时间。"
                ),
                story_intro_en=(
                    "You are short on time and want to order food to go. You need "
                    "to quickly explain what you want, mention any dietary "
                    "restrictions, and confirm the packaging and wait time."
                ),
                opening_message="Hi there, are you looking to order something to go?",
            ),
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
        story_seeds=[
            StorySeed(
                seed_id="meeting_standup",
                label_zh="Stand-up 汇报进度",
                story_intro_zh=(
                    "现在是每天的站会时间，团队负责人正依次询问每个人的进展。轮到你时，"
                    "需要简洁说明你昨天完成了什么、今天打算做什么。"
                ),
                story_intro_en=(
                    "It is time for the daily stand-up, and the team lead is going "
                    "around asking for updates. When it is your turn, you need to "
                    "briefly share what you finished yesterday and what you plan to "
                    "do today."
                ),
                opening_message="Let's start with your update. What progress have you made since our last stand-up?",
            ),
            StorySeed(
                seed_id="meeting_project_sync",
                label_zh="项目同步会",
                story_intro_zh=(
                    "这是一个跨团队的项目同步会，团队负责人想了解整体进度，并确认接下来"
                    "一周需要协调的事项。"
                ),
                story_intro_en=(
                    "This is a cross-team project sync meeting. The team lead wants "
                    "an overview of the current progress and to confirm what needs "
                    "to be coordinated for the coming week."
                ),
                opening_message="Thanks for joining the sync. Could you give us a quick overview of where the project stands right now?",
            ),
            StorySeed(
                seed_id="meeting_raise_blocker",
                label_zh="提出 Blocker",
                story_intro_zh=(
                    "你这周遇到了一个卡住进度的问题，需要在小组会议上向团队负责人说明"
                    "这个 blocker，并讨论可能的解决办法。"
                ),
                story_intro_en=(
                    "You ran into an issue this week that is blocking your "
                    "progress, and you need to explain this blocker to your team "
                    "lead in the team meeting and discuss possible solutions."
                ),
                opening_message="Before we move on, is there anything blocking your work this week that we should talk through?",
            ),
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
        story_seeds=[
            StorySeed(
                seed_id="travel_hotel_checkin",
                label_zh="酒店入住",
                story_intro_zh=(
                    "你刚抵达酒店，比预计的时间早到了一些。前台工作人员正在核对你的"
                    "预订信息，你需要说明情况并询问能否提前办理入住。"
                ),
                story_intro_en=(
                    "You have just arrived at the hotel a bit earlier than "
                    "expected. The front desk staff is checking your reservation, "
                    "and you need to explain the situation and ask about early "
                    "check-in."
                ),
                opening_message="Hello! Welcome to our hotel. Could I have your name and reservation details, please?",
            ),
            StorySeed(
                seed_id="travel_directions",
                label_zh="问路",
                story_intro_zh=(
                    "你在一个陌生的城市迷了路，看到路边有一位看起来很热心的当地人，"
                    "于是上前询问怎么去你要去的地方。"
                ),
                story_intro_en=(
                    "You are lost in an unfamiliar city and notice a "
                    "friendly-looking local nearby, so you approach them to ask how "
                    "to get to the place you are heading."
                ),
                opening_message="Hi, excuse me — you look like you might know this area. Where are you trying to go?",
            ),
            StorySeed(
                seed_id="travel_airport",
                label_zh="机场 / 车站沟通",
                story_intro_zh=(
                    "你在机场遇到了航班延误的问题，需要找工作人员了解最新情况，并确认"
                    "接下来该怎么安排。"
                ),
                story_intro_en=(
                    "You run into a flight delay at the airport and need to find a "
                    "staff member to understand the latest situation and figure out "
                    "what to do next."
                ),
                opening_message="Hello, I understand you have a question about your flight. How can I help you today?",
            ),
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
        story_seeds=[
            StorySeed(
                seed_id="daily_cafe_classmate",
                label_zh="咖啡馆偶遇同学",
                story_intro_zh=(
                    "周六下午，你在常去的咖啡馆里偶遇了一位很久没联系的同学。你们找了"
                    "张靠窗的桌子坐下，准备聊聊最近的生活。"
                ),
                story_intro_en=(
                    "On a Saturday afternoon, you run into a classmate you have not "
                    "seen for a while at your favorite cafe. You both sit by the "
                    "window and start catching up on recent life."
                ),
                opening_message="Hey, what a surprise seeing you here! It's been a while — how have you been lately?",
            ),
            StorySeed(
                seed_id="daily_after_class",
                label_zh="下课后和朋友聊天",
                story_intro_zh=(
                    "刚下课，你和朋友一起走出教室，准备去吃午饭。路上你们随意聊起这周"
                    "的课程、作业和周末的安排。"
                ),
                story_intro_en=(
                    "Class has just ended, and you are walking out with a friend to "
                    "grab lunch. On the way, you casually chat about this week's "
                    "classes, homework, and weekend plans."
                ),
                opening_message="That class felt pretty long today, right? What are you up to for lunch?",
            ),
            StorySeed(
                seed_id="daily_weekend_plans",
                label_zh="周末计划闲聊",
                story_intro_zh=(
                    "周五晚上，你和朋友通话，随口聊起这个周末打算做什么。气氛很轻松，"
                    "你们可以谈兴趣爱好、休息计划或者想去的地方。"
                ),
                story_intro_en=(
                    "It is Friday evening, and you are chatting with a friend about "
                    "weekend plans. The mood is relaxed, and you can talk about "
                    "hobbies, rest, or places you would like to visit."
                ),
                opening_message="Hi! Do you have any plans for the weekend, or are you just going to relax?",
            ),
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


def find_story_seed(scenario_id: str, seed_id: str | None) -> StorySeed | None:
    if not seed_id:
        return None
    config = get_scenario_prompt_config(scenario_id)
    for seed in config.story_seeds:
        if seed.seed_id == seed_id:
            return seed
    return None


def list_story_seeds(scenario_id: str) -> list[StorySeed]:
    return list(get_scenario_prompt_config(scenario_id).story_seeds)
