import type { Feedback, Message, Scenario, SessionSummary } from "./coaching";

const STORAGE_USER_ID = "anytime_user_id";
const STORAGE_USERNAME = "anytime_username";
const STORAGE_PENDING_HISTORY = "anytime_pending_history";

export type AuthUser = {
  userId: string;
  username: string;
  createdAt: string;
};

export type HistorySessionItem = {
  sessionId: string;
  scenarioId: string;
  scenarioTitle: string;
  startedAt: string;
  overallScore: number | null;
  summaryPreview: string | null;
  provider: string;
};

export type HistorySessionDetail = {
  sessionId: string;
  scenarioId: string;
  scenarioTitle: string;
  storyIntro: string | null;
  storyIntroZh: string | null;
  storyIntroEn: string | null;
  startedAt: string;
  endedAt: string | null;
  score: number | null;
  overallScore: number | null;
  summary: string | null;
  summaryJson: Record<string, unknown> | null;
  provider: string;
  messages: { role: string; content: string }[];
  feedbacks: {
    userMessage: string | null;
    feedbackJson: Record<string, unknown> | null;
    score: number | null;
  }[];
};

export function loadStoredUser(): AuthUser | null {
  try {
    const userId = localStorage.getItem(STORAGE_USER_ID);
    const username = localStorage.getItem(STORAGE_USERNAME);
    if (userId && username) {
      return { userId, username, createdAt: "" };
    }
  } catch {
    // localStorage may be unavailable in some environments.
  }
  return null;
}

export function storeUser(user: AuthUser): void {
  try {
    localStorage.setItem(STORAGE_USER_ID, user.userId);
    localStorage.setItem(STORAGE_USERNAME, user.username);
  } catch {
    // ignore
  }
}

export function clearStoredUser(): void {
  try {
    localStorage.removeItem(STORAGE_USER_ID);
    localStorage.removeItem(STORAGE_USERNAME);
  } catch {
    // ignore
  }
}

const API_BASE = (() => {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (!raw) return "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
})();

async function historyRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const resp = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      signal: controller.signal,
    });
    if (!resp.ok) throw new HistoryRequestError(resp.status, `HTTP ${resp.status}`);
    return (await resp.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

export function loadPendingHistory(): Omit<SaveHistoryPayload, "userId"> | null {
  try {
    const raw = localStorage.getItem(STORAGE_PENDING_HISTORY);
    if (!raw) return null;
    return JSON.parse(raw) as Omit<SaveHistoryPayload, "userId">;
  } catch {
    return null;
  }
}

export function storePendingHistory(payload: Omit<SaveHistoryPayload, "userId">): void {
  try {
    localStorage.setItem(STORAGE_PENDING_HISTORY, JSON.stringify(payload));
  } catch {
    // ignore
  }
}

export function clearPendingHistory(): void {
  try {
    localStorage.removeItem(STORAGE_PENDING_HISTORY);
  } catch {
    // ignore
  }
}

export class HistoryRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "HistoryRequestError";
    this.status = status;
  }
}

type ApiAuthUser = {
  user_id: string;
  username: string;
  created_at: string;
};

export async function registerUser(username: string, password: string): Promise<AuthUser> {
  const data = await historyRequest<ApiAuthUser>("/api/users/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return fromApiUser(data);
}

export async function loginUser(username: string, password: string): Promise<AuthUser> {
  const data = await historyRequest<ApiAuthUser>("/api/users/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return fromApiUser(data);
}

export async function fetchUser(userId: string): Promise<AuthUser> {
  const data = await historyRequest<ApiAuthUser>(`/api/users/${encodeURIComponent(userId)}`);
  return fromApiUser(data);
}

type ApiSessionItem = {
  session_id: string;
  scenario_id: string;
  scenario_title: string;
  started_at: string;
  overall_score: number | null;
  summary_preview: string | null;
  provider: string;
};

type ApiSessionDetail = {
  session_id: string;
  scenario_id: string;
  scenario_title: string;
  story_intro: string | null;
  story_intro_zh: string | null;
  story_intro_en: string | null;
  started_at: string;
  ended_at: string | null;
  score: number | null;
  overall_score: number | null;
  summary: string | null;
  summary_json: Record<string, unknown> | null;
  provider: string;
  messages: { role: string; content: string }[];
  feedbacks: {
    user_message: string | null;
    feedback_json: Record<string, unknown> | null;
    score: number | null;
  }[];
};

export type SaveHistoryPayload = {
  userId: string;
  sessionId: string;
  scenario: Scenario;
  messages: Message[];
  feedbacks: Feedback[];
  summary: SessionSummary;
  provider: string;
};

export async function saveSessionHistory(payload: SaveHistoryPayload): Promise<HistorySessionItem> {
  const scoreMap = payload.summary.scores as Record<string, number>;
  const overallScore = resolveOverallScore(scoreMap);
  const body = {
    user_id: payload.userId,
    session_id: payload.sessionId,
    scenario_id: payload.scenario.id,
    scenario_title: payload.scenario.title,
    story_intro: payload.scenario.storyIntroZh ?? payload.scenario.storyIntroEn ?? null,
    story_intro_zh: payload.scenario.storyIntroZh ?? null,
    story_intro_en: payload.scenario.storyIntroEn ?? null,
    messages: payload.messages.map((m) => ({
      role: m.sender === "ai" ? "assistant" : "user",
      content: m.text,
    })),
    feedbacks: payload.feedbacks.map((f) => ({
      user_message: f.whatYouSaid,
      feedback_json: {
        issue: f.issue,
        why: f.why,
        recommended_english: f.recommendedEnglish,
        more_natural_option: f.moreNaturalOption,
        score_breakdown: f.scoreBreakdown,
        provider: f.provider,
        pronunciation_assessment: f.pronunciation
          ? {
              provider: f.pronunciation.provider,
              pronunciation_score: f.pronunciation.pronunciationScore,
              fluency_score: f.pronunciation.fluencyScore,
              accuracy_score: f.pronunciation.accuracyScore,
              completeness_score: f.pronunciation.completenessScore,
              rhythm_score: f.pronunciation.rhythmScore ?? null,
              overall_score: f.pronunciation.overallScore,
              feedback_zh: f.pronunciation.feedbackZh,
              strengths: f.pronunciation.strengths,
              improvement_tips: f.pronunciation.improvementTips,
              word_tips: f.pronunciation.wordTips,
              is_fallback: f.pronunciation.isFallback,
            }
          : null,
        pronunciation_input_mode: f.pronunciationInputMode ?? "text",
      },
      score: f.score,
    })),
    summary: {
      summary: payload.summary.overallPerformance,
      strengths: payload.summary.strengths,
      repeated_issues: payload.summary.repeatedIssues,
      better_expressions: payload.summary.betterExpressions,
      scores: payload.summary.scores,
    },
    summary_text: payload.summary.overallPerformance,
    scores: {
      ...payload.summary.scores,
      overall: overallScore,
    },
    score: overallScore,
    overall_score: overallScore,
    provider: payload.provider,
  };

  const data = await historyRequest<ApiSessionItem>("/api/history/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });

  return fromApiSessionItem(data);
}

function resolveOverallScore(scores: Record<string, number>): number | null {
  const explicit = scores.overall ?? scores["综合"] ?? scores["缁煎悎"];
  if (typeof explicit === "number" && Number.isFinite(explicit)) {
    return explicit;
  }

  const values = Object.values(scores).filter((value) => typeof value === "number" && Number.isFinite(value));
  if (values.length === 0) return null;
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

export async function fetchSessionHistory(userId: string): Promise<HistorySessionItem[]> {
  const items = await historyRequest<ApiSessionItem[]>(`/api/history/sessions?user_id=${encodeURIComponent(userId)}`);
  return items.map(fromApiSessionItem);
}

export async function fetchSessionDetail(sessionId: string): Promise<HistorySessionDetail> {
  const data = await historyRequest<ApiSessionDetail>(`/api/history/sessions/${encodeURIComponent(sessionId)}`);
  return {
    sessionId: data.session_id,
    scenarioId: data.scenario_id,
    scenarioTitle: data.scenario_title,
    storyIntro: data.story_intro,
    storyIntroZh: data.story_intro_zh,
    storyIntroEn: data.story_intro_en,
    startedAt: data.started_at,
    endedAt: data.ended_at,
    score: data.score,
    overallScore: data.overall_score,
    summary: data.summary,
    summaryJson: data.summary_json,
    provider: data.provider,
    messages: data.messages,
    feedbacks: data.feedbacks.map((f) => ({
      userMessage: f.user_message,
      feedbackJson: f.feedback_json,
      score: f.score,
    })),
  };
}

function fromApiUser(data: ApiAuthUser): AuthUser {
  return {
    userId: data.user_id,
    username: data.username,
    createdAt: data.created_at,
  };
}

function fromApiSessionItem(data: ApiSessionItem): HistorySessionItem {
  return {
    sessionId: data.session_id,
    scenarioId: data.scenario_id,
    scenarioTitle: data.scenario_title,
    startedAt: data.started_at,
    overallScore: data.overall_score,
    summaryPreview: data.summary_preview,
    provider: data.provider,
  };
}

export function providerLabel(provider: string): string {
  if (provider === "llm") return "LLM";
  if (provider === "mock") return "Mock";
  return "本地";
}

export function formatDateTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}
