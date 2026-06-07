export type Sender = "ai" | "user";

export type Scenario = {
  id: string;
  scenarioId: string;
  title: string;
  englishTitle: string;
  description: string;
  aiRole: string;
  userRole: string;
  goal: string;
  storySeedId: string;
  storyIntroZh: string;
  storyIntroEn: string;
  level: string;
  duration: string;
  focus: string[];
  usefulExpressions: string[];
  openingLine: string;
  replies: string[];
};

export type Message = { id: number; sender: Sender; text: string };
export type PracticeSession = {
  sessionId: string;
  scenarioId: string;
  storySeedId: string;
  storyIntroZh: string;
  storyIntroEn: string;
  openingMessage: string;
  messages: Message[];
  createdAt: string;
};
export type FeedbackScoreBreakdown = Record<"语法" | "自然度" | "贴合度" | "清晰度", number>;
export type Feedback = {
  id: number;
  whatYouSaid: string;
  userIntent: string;
  recommendedEnglish: string;
  issue: string;
  why: string;
  moreNaturalOption: string;
  score: number;
  scoreBreakdown: FeedbackScoreBreakdown;
  provider: string;
  fallbackReason?: string | null;
};
export type ScoreBreakdown = Record<"语法" | "表达" | "流畅" | "完成度" | "综合", number>;
export type SessionSummary = {
  overallPerformance: string;
  strengths: string[];
  repeatedIssues: string[];
  betterExpressions: string[];
  scores: ScoreBreakdown;
  provider: string;
  fallbackReason?: string | null;
};

type ApiScenario = {
  id: string;
  scenario_id: string;
  title: string;
  title_zh: string;
  level: string;
  ai_role: string;
  user_role: string;
  goal: string;
  story_seed_id: string;
  story_intro_zh: string;
  story_intro_en: string;
  opening_line: string;
  opening_message: string;
  conversation_style: string;
  feedback_focus: string[];
  useful_expressions: string[];
};

type ApiChatMessage = { role: "user" | "assistant"; content: string };
type ApiSession = {
  session_id: string;
  scenario_id: string;
  story_seed_id: string;
  story_intro_zh: string;
  story_intro_en: string;
  opening_message: string;
  messages: ApiChatMessage[];
  created_at: string;
};
type ApiFeedbackScoreBreakdown = {
  grammar: number;
  naturalness: number;
  relevance: number;
  clarity: number;
};
type ApiFeedback = {
  what_you_said: string;
  user_intent: string;
  recommended_english: string;
  issue: string;
  why: string;
  more_natural_option: string;
  score: number;
  score_breakdown: ApiFeedbackScoreBreakdown;
  provider: string;
  fallback_reason?: string | null;
};
type ApiChatResponse = { reply: ApiChatMessage; provider: string; fallback_reason?: string | null; quick_feedback?: ApiFeedback };
type ApiSummaryResponse = {
  summary: string;
  strengths: string[];
  repeated_issues: string[];
  better_expressions: string[];
  scores: {
    grammar: number;
    expression: number;
    fluency: number;
    scenario_completion: number;
    overall: number;
  };
  provider: string;
  fallback_reason?: string | null;
};

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
// The backend gives the LLM provider up to 90s before falling back to mock
// (see backend/app/llm_provider.py LLM_TIMEOUT_SECONDS). A real LLM-backed
// /api/chat, /api/feedback, or /api/summary call regularly takes 8-15s, so the
// frontend timeout must stay above the backend's own ceiling —
// otherwise every real reply gets aborted client-side and treated as a backend
// failure, even though the backend would have answered a few seconds later.
const REQUEST_TIMEOUTS_MS: Record<string, number> = {
  "/api/health": 5000,
  "/api/scenarios": 10000,
  "/api/sessions": 10000,
  "/api/chat": 120000,
  "/api/feedback": 120000,
  "/api/summary": 150000,
};

export const localScenarios: Scenario[] = [
  {
    id: "interview",
    scenarioId: "interview",
    title: "面试沟通",
    englishTitle: "Interview",
    description: "练习自我介绍、项目经历和职业动机，回答更自然、更有结构。",
    aiRole: "招聘经理",
    userRole: "候选人",
    goal: "清楚介绍自己，说明经验价值，并提出一个专业追问。",
    storySeedId: "interview_first_round",
    storyIntroZh: "你正在参加一场初级岗位的视频面试。招聘经理已经看过简历，希望听到你用清楚、有信心的英文讲出背景、项目和动机。",
    storyIntroEn:
      "You are taking part in a video interview for an entry-level role. The hiring manager has already read your resume and wants to hear you describe your background, projects, and motivation in clear, confident English.",
    level: "进阶",
    duration: "8 分钟",
    focus: ["自我介绍", "STAR 表达", "职业动机"],
    usefulExpressions: ["I contributed to...", "One challenge I faced was...", "I am interested in this role because..."],
    openingLine:
      "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?",
    replies: [
      "Thanks for sharing that. Can you describe one project where you made a clear impact?",
      "That sounds useful. What challenge did you face, and how did you handle it?",
      "Good example. Before we finish, what would you like to know about the team or role?",
    ],
  },
  {
    id: "restaurant",
    scenarioId: "ordering_food",
    title: "餐厅点餐",
    englishTitle: "Ordering Food",
    description: "从询问推荐到确认偏好，练习礼貌、清楚的日常服务场景表达。",
    aiRole: "餐厅服务员",
    userRole: "顾客",
    goal: "点餐、询问推荐、说明忌口或偏好，并确认最终订单。",
    storySeedId: "ordering_cafe",
    storyIntroZh: "午餐时间你走进一家有点忙的咖啡店。队伍在往前移动，你需要礼貌地询问推荐、说明偏好，并确认最终点单。",
    storyIntroEn:
      "It's lunchtime and you walk into a slightly busy cafe. The line is moving forward, so you need to politely ask for recommendations, explain your preferences, and confirm your final order.",
    level: "入门",
    duration: "6 分钟",
    focus: ["礼貌请求", "偏好说明", "订单确认"],
    usefulExpressions: ["I'd like...", "Could I have...", "Does this come with..."],
    openingLine: "Welcome! Are you ready to order, or would you like a few recommendations first?",
    replies: [
      "Of course. Our grilled salmon is popular today. Do you have any allergies or preferences?",
      "Great choice. Would you like that with rice, salad, or roasted vegetables?",
      "Perfect. I will place that order for you. Would you like anything to drink?",
    ],
  },
  {
    id: "meeting",
    scenarioId: "meeting",
    title: "会议汇报",
    englishTitle: "Meeting",
    description: "练习汇报进展、说明阻塞点、请求支持，并对齐下一步。",
    aiRole: "团队负责人",
    userRole: "团队成员",
    goal: "给出进展更新，说明问题，确认下一步和完成时间。",
    storySeedId: "meeting_standup",
    storyIntroZh: "你正在参加一个简短的团队站会。团队负责人需要你简洁说明进展、阻塞点，以及接下来可以跟进的行动。",
    storyIntroEn:
      "You are joining a short team stand-up meeting. The team lead needs you to briefly share your progress, any blockers, and the next actions you plan to follow up on.",
    level: "进阶",
    duration: "8 分钟",
    focus: ["进度汇报", "问题说明", "下一步对齐"],
    usefulExpressions: ["The main blocker is...", "Could you clarify...", "I'll follow up by..."],
    openingLine: "Let's start with your update. What progress have you made since our last meeting?",
    replies: [
      "Thanks for the update. Is anything blocking the remaining work right now?",
      "That is clear. What support do you need from the team this week?",
      "Good. Please confirm the next step and when you expect to finish it.",
    ],
  },
];

const LEVEL_ZH: Record<string, string> = {
  // single words
  beginner: "入门", elementary: "入门", basic: "入门",
  intermediate: "进阶", medium: "进阶",
  advanced: "高级", expert: "高级", proficient: "高级",
  // compound phrases from backend catalog
  "beginner to intermediate": "入门",
  "intermediate to upper-intermediate": "进阶",
  "intermediate to advanced": "进阶",
  "upper-intermediate": "进阶",
  "upper-intermediate to advanced": "高级",
};

const FOCUS_ZH: Record<string, string> = {
  // grammar
  "tense consistency": "时态一致",
  "subject-verb agreement": "主谓一致",
  "article usage": "冠词用法",
  "articles": "冠词",
  "countable nouns": "可数名词",
  "modal verbs": "情态动词",
  "polite modal verbs": "礼貌情态动词",
  "present perfect": "现在完成时",
  "past tense": "过去时",
  "future plans": "将来时表达",
  "prepositions": "介词",
  "common prepositions": "常用介词",
  "prepositions of place and time": "时间地点介词",
  "word order": "语序",
  "basic sentence structure": "基础句式",
  "tense use": "时态使用",
  // expression
  "professional wording": "专业措辞",
  "structured answers": "结构化回答",
  "professional update phrases": "职场更新用语",
  "clear requests": "清晰请求",
  "natural ordering phrases": "自然点餐用语",
  "polite question forms": "礼貌疑问句",
  "question forms": "疑问句形式",
  "travel vocabulary": "旅行词汇",
  "clear problem descriptions": "清晰问题描述",
  "natural small talk": "日常闲聊",
};

function normalizeLevel(raw: string): string {
  return LEVEL_ZH[raw.toLowerCase()] ?? raw;
}

function normalizeFocus(tag: string): string {
  return FOCUS_ZH[tag.toLowerCase()] ?? tag;
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const apiScenarios = await request<ApiScenario[]>("/api/scenarios");
  const localById = new Map(localScenarios.map((scenario) => [scenario.id, scenario]));

  return apiScenarios.map((scenario) => {
    const local = localById.get(scenario.id);
    return {
      id: scenario.id,
      scenarioId: scenario.scenario_id,
      title: local?.title ?? `${scenario.title_zh}练习`,
      englishTitle: scenario.title,
      description: local?.description ?? scenario.conversation_style,
      aiRole: local?.aiRole ?? scenario.ai_role,
      userRole: local?.userRole ?? scenario.user_role,
      goal: local?.goal ?? scenario.goal,
      storySeedId: scenario.story_seed_id,
      storyIntroZh: scenario.story_intro_zh,
      storyIntroEn: scenario.story_intro_en,
      level: local?.level ?? normalizeLevel(scenario.level),
      duration: local?.duration ?? "8 分钟",
      focus: local?.focus ?? scenario.feedback_focus.map(normalizeFocus),
      usefulExpressions: scenario.useful_expressions,
      openingLine: scenario.opening_message ?? scenario.opening_line,
      replies: local?.replies ?? [scenario.opening_line],
    };
  });
}

export async function startPracticeSession(scenario: Scenario): Promise<PracticeSession> {
  const response = await request<ApiSession>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenario.id }),
  });

  return {
    sessionId: response.session_id,
    scenarioId: response.scenario_id,
    storySeedId: response.story_seed_id,
    storyIntroZh: response.story_intro_zh,
    storyIntroEn: response.story_intro_en,
    openingMessage: sanitizeAiText(response.opening_message),
    messages: response.messages.map(fromApiMessage),
    createdAt: response.created_at,
  };
}

export async function sendChatMessage(
  scenario: Scenario,
  sessionId: string | null,
  conversationHistory: Message[],
  latestUserMessage: Message,
): Promise<{ message: Message; provider: string; fallbackReason?: string | null }> {
  const response = await request<ApiChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      scenario_id: scenario.id,
      latest_user_message: latestUserMessage.text,
      conversation_history: toApiMessages(conversationHistory),
    }),
  });

  return {
    message: { id: Date.now() + 1, sender: "ai", text: sanitizeAiText(response.reply.content) },
    provider: response.provider ?? response.quick_feedback?.provider ?? "mock",
    fallbackReason: response.fallback_reason ?? response.quick_feedback?.fallback_reason ?? null,
  };
}

export async function fetchTurnFeedback(
  scenario: Scenario,
  sessionId: string | null,
  conversationHistory: Message[],
  message: Message,
): Promise<Feedback> {
  const response = await request<ApiFeedback>("/api/feedback", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      scenario_id: scenario.id,
      latest_user_message: message.text,
      conversation_history: toApiMessages(conversationHistory),
    }),
  });

  return {
    id: message.id,
    whatYouSaid: response.what_you_said,
    userIntent: response.user_intent,
    recommendedEnglish: sanitizeAiText(response.recommended_english),
    issue: sanitizeAiText(response.issue),
    why: sanitizeAiText(response.why),
    moreNaturalOption: sanitizeAiText(response.more_natural_option),
    score: response.score,
    scoreBreakdown: {
      "语法": response.score_breakdown.grammar,
      "自然度": response.score_breakdown.naturalness,
      "贴合度": response.score_breakdown.relevance,
      "清晰度": response.score_breakdown.clarity,
    },
    provider: response.provider,
    fallbackReason: response.fallback_reason ?? null,
  };
}

export async function fetchSessionSummary(scenario: Scenario, messages: Message[]): Promise<SessionSummary> {
  const response = await request<ApiSummaryResponse>("/api/summary", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenario.id, conversation_history: toApiMessages(messages) }),
  });

  return {
    overallPerformance: response.summary,
    strengths: response.strengths,
    repeatedIssues: response.repeated_issues,
    betterExpressions: response.better_expressions,
    scores: {
      "语法": response.scores.grammar,
      "表达": response.scores.expression,
      "流畅": response.scores.fluency,
      "完成度": response.scores.scenario_completion,
      "综合": response.scores.overall,
    },
    provider: response.provider,
    fallbackReason: response.fallback_reason ?? null,
  };
}

export function createLocalReply(scenario: Scenario, messages: Message[]): Message {
  const turn = Math.max(0, messages.filter((message) => message.sender === "user").length - 1);
  return { id: Date.now() + 1, sender: "ai", text: scenario.replies[turn % scenario.replies.length] };
}

export function createLocalSummary(messages: Message[], feedback: Feedback[]): SessionSummary {
  const avg = feedback.length ? Math.round(feedback.reduce((sum, item) => sum + item.score, 0) / feedback.length) : 82;
  const turns = messages.filter((message) => message.sender === "user").length;

  return {
    overallPerformance: "你已经完成本次场景练习，回答方向清楚。下一步可以尝试增加细节、连接词和更自然的礼貌表达。",
    strengths: ["能围绕场景目标给出直接回答。", "对话没有偏离角色设定，适合继续扩展。", "已经使用了可理解的基础职场 / 日常词汇。"],
    repeatedIssues: feedback.length ? feedback.map((item) => item.issue).slice(-3) : ["建议至少完成 2-3 轮对话，让总结更有参考价值。"],
    betterExpressions: [
      "I would like to learn more about...",
      "Could you clarify what you mean by...?",
      "My main contribution was...",
      "I would prefer..., if possible.",
    ],
    scores: {
      "语法": Math.min(96, avg + 2),
      "表达": Math.min(94, avg + 4),
      "流畅": turns > 1 ? 86 : 78,
      "完成度": turns > 2 ? 90 : 82,
      "综合": Math.round((avg + 86 + 84 + 88) / 4),
    },
    provider: "local-fallback",
    fallbackReason: "frontend_api_unavailable",
  };
}

function sanitizeAiText(text: string): string {
  return text
    .replace(/—|―/g, " - ") // em dash → spaced hyphen
    .replace(/–/g, "-")           // en dash → hyphen
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function toApiMessages(messages: Message[]): ApiChatMessage[] {
  return messages.map((message) => ({
    role: message.sender === "ai" ? "assistant" : "user",
    content: message.text,
  }));
}

function fromApiMessage(message: ApiChatMessage, index: number): Message {
  return {
    id: Date.now() + index,
    sender: message.role === "assistant" ? "ai" : "user",
    text: message.content,
  };
}

export type ApiFailureReason = "timeout" | "network" | "http" | "parse";

export class ApiRequestError extends Error {
  readonly endpoint: string;
  readonly status: number | null;
  readonly reason: ApiFailureReason;

  constructor(endpoint: string, reason: ApiFailureReason, status: number | null) {
    super(
      reason === "http"
        ? `${endpoint} responded with HTTP ${status}`
        : reason === "timeout"
          ? `${endpoint} timed out`
          : reason === "parse"
            ? `${endpoint} returned invalid JSON`
          : `${endpoint} could not be reached (network error)`,
    );
    this.name = "ApiRequestError";
    this.endpoint = endpoint;
    this.reason = reason;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = REQUEST_TIMEOUTS_MS[path] ?? 15000;
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const url = `${API_BASE_URL}${path}`;

  try {
    let response: Response;
    try {
      response = await fetch(url, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
        signal: controller.signal,
      });
    } catch {
      const reason: ApiFailureReason = controller.signal.aborted ? "timeout" : "network";
      throw reportFailure(new ApiRequestError(path, reason, null));
    }

    if (!response.ok) {
      throw reportFailure(new ApiRequestError(path, "http", response.status));
    }

    try {
      return (await response.json()) as T;
    } catch {
      throw reportFailure(new ApiRequestError(path, "parse", response.status));
    }
  } finally {
    window.clearTimeout(timeout);
  }
}

// Surfaces exactly which endpoint failed, why, and (for HTTP errors) the
// status code — so a 422 schema mismatch, a timeout, and "backend not running"
// are distinguishable in the console instead of all collapsing into the same
// generic "本地练习模式" banner. Logs only the endpoint path and failure
// classification: never headers, bodies, API keys, or tokens.
function reportFailure(error: ApiRequestError): ApiRequestError {
  if (import.meta.env.DEV) {
    console.error(
      `[coaching-api] ${error.endpoint} -> ${error.reason}` +
        (error.status !== null ? ` (HTTP ${error.status})` : "") +
        " — falling back to local mode for this call. Check that the backend is running and reachable at the proxied /api path.",
    );
  }
  return error;
}

function normalizeApiBaseUrl(value: string | undefined): string {
  if (!value) return "";
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
