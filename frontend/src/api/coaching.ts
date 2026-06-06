export type Sender = "ai" | "user";

export type Scenario = {
  id: string;
  title: string;
  englishTitle: string;
  description: string;
  aiRole: string;
  userRole: string;
  goal: string;
  level: string;
  duration: string;
  focus: string[];
  openingLine: string;
  replies: string[];
};

export type Message = { id: number; sender: Sender; text: string };
export type Feedback = { id: number; corrected: string; issue: string; better: string; score: number };
export type ScoreBreakdown = Record<"语法" | "表达" | "流畅" | "完成度" | "综合", number>;
export type SessionSummary = {
  overallPerformance: string;
  strengths: string[];
  repeatedIssues: string[];
  betterExpressions: string[];
  scores: ScoreBreakdown;
};

type ApiScenario = {
  id: string;
  title: string;
  title_zh: string;
  level: string;
  ai_role: string;
  user_role: string;
  goal: string;
  opening_line: string;
  conversation_style: string;
  feedback_focus: string[];
};

type ApiChatMessage = { role: "user" | "assistant"; content: string };
type ApiFeedback = { corrected_sentence: string; issue: string; better_expression: string; score: number };
type ApiChatResponse = { reply: ApiChatMessage };
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
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 3500;

export const localScenarios: Scenario[] = [
  {
    id: "interview",
    title: "面试沟通",
    englishTitle: "Interview",
    description: "练习自我介绍、项目经历和职业动机，回答更自然、更有结构。",
    aiRole: "招聘经理",
    userRole: "候选人",
    goal: "清楚介绍自己，说明经验价值，并提出一个专业追问。",
    level: "进阶",
    duration: "8 分钟",
    focus: ["自我介绍", "STAR 表达", "职业动机"],
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
    title: "餐厅点餐",
    englishTitle: "Ordering Food",
    description: "从询问推荐到确认偏好，练习礼貌、清楚的日常服务场景表达。",
    aiRole: "餐厅服务员",
    userRole: "顾客",
    goal: "点餐、询问推荐、说明忌口或偏好，并确认最终订单。",
    level: "入门",
    duration: "6 分钟",
    focus: ["礼貌请求", "偏好说明", "订单确认"],
    openingLine: "Welcome! Are you ready to order, or would you like a few recommendations first?",
    replies: [
      "Of course. Our grilled salmon is popular today. Do you have any allergies or preferences?",
      "Great choice. Would you like that with rice, salad, or roasted vegetables?",
      "Perfect. I will place that order for you. Would you like anything to drink?",
    ],
  },
  {
    id: "meeting",
    title: "会议汇报",
    englishTitle: "Meeting",
    description: "练习汇报进展、说明阻塞点、请求支持，并对齐下一步。",
    aiRole: "团队负责人",
    userRole: "团队成员",
    goal: "给出进展更新，说明问题，确认下一步和完成时间。",
    level: "进阶",
    duration: "8 分钟",
    focus: ["进度汇报", "问题说明", "下一步对齐"],
    openingLine: "Let's start with your update. What progress have you made since our last meeting?",
    replies: [
      "Thanks for the update. Is anything blocking the remaining work right now?",
      "That is clear. What support do you need from the team this week?",
      "Good. Please confirm the next step and when you expect to finish it.",
    ],
  },
];

export async function fetchScenarios(): Promise<Scenario[]> {
  const apiScenarios = await request<ApiScenario[]>("/api/scenarios");
  const localById = new Map(localScenarios.map((scenario) => [scenario.id, scenario]));

  return apiScenarios.map((scenario) => {
    const local = localById.get(scenario.id);
    return {
      id: scenario.id,
      title: local?.title ?? `${scenario.title_zh}练习`,
      englishTitle: scenario.title,
      description: local?.description ?? scenario.conversation_style,
      aiRole: local?.aiRole ?? scenario.ai_role,
      userRole: local?.userRole ?? scenario.user_role,
      goal: local?.goal ?? scenario.goal,
      level: local?.level ?? scenario.level,
      duration: local?.duration ?? "8 分钟",
      focus: local?.focus ?? scenario.feedback_focus,
      openingLine: scenario.opening_line,
      replies: local?.replies ?? [scenario.opening_line],
    };
  });
}

export async function sendChatMessage(scenario: Scenario, messages: Message[]): Promise<Message> {
  const response = await request<ApiChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenario.id, messages: toApiMessages(messages) }),
  });

  return { id: Date.now() + 1, sender: "ai", text: response.reply.content };
}

export async function fetchTurnFeedback(scenario: Scenario, message: Message): Promise<Feedback> {
  const response = await request<ApiFeedback>("/api/feedback", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenario.id, message: message.text }),
  });

  return {
    id: message.id,
    corrected: response.corrected_sentence,
    issue: response.issue,
    better: response.better_expression,
    score: response.score,
  };
}

export async function fetchSessionSummary(scenario: Scenario, messages: Message[]): Promise<SessionSummary> {
  const response = await request<ApiSummaryResponse>("/api/summary", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenario.id, messages: toApiMessages(messages) }),
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
  };
}

export function createLocalReply(scenario: Scenario, messages: Message[]): Message {
  const turn = Math.max(0, messages.filter((message) => message.sender === "user").length - 1);
  return { id: Date.now() + 1, sender: "ai", text: scenario.replies[turn % scenario.replies.length] };
}

export function createLocalFeedback(input: string, id = Date.now()): Feedback {
  const text = input.trim();
  const sentence = text.endsWith(".") || text.endsWith("?") || text.endsWith("!") ? text : `${text}.`;
  const corrected = sentence.charAt(0).toUpperCase() + sentence.slice(1);

  return {
    id,
    corrected,
    issue: "后端暂不可用，当前使用前端本地 mock：句子意思清楚，可继续补充细节和自然连接词。",
    better: "I would like to add one specific example to explain my answer.",
    score: Math.min(94, 78 + Math.min(10, Math.floor(text.length / 16))),
  };
}

export function createLocalSummary(messages: Message[], feedback: Feedback[]): SessionSummary {
  const avg = feedback.length ? Math.round(feedback.reduce((sum, item) => sum + item.score, 0) / feedback.length) : 82;
  const turns = messages.filter((message) => message.sender === "user").length;

  return {
    overallPerformance: "你已经完成本次场景练习，回答方向清楚。下一步可以尝试增加细节、连接词和更自然的礼貌表达。",
    strengths: ["能围绕场景目标给出直接回答。", "对话没有偏离角色设定，适合继续扩展。", "已经使用了可理解的基础职场 / 日常词汇。"],
    repeatedIssues: feedback.length ? feedback.map((item) => item.issue).slice(0, 3) : ["建议至少完成 2-3 轮对话，让总结更有参考价值。"],
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
  };
}

function toApiMessages(messages: Message[]): ApiChatMessage[] {
  return messages.map((message) => ({
    role: message.sender === "ai" ? "assistant" : "user",
    content: message.text,
  }));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}
