import type { Feedback, Message, Scenario, SessionSummary } from "./coaching";

const STORAGE_USER_ID = "anytime_user_id";
const STORAGE_DISPLAY_NAME = "anytime_display_name";

export type GuestUser = {
  userId: string;
  displayName: string;
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
  storyIntroZh: string | null;
  storyIntroEn: string | null;
  startedAt: string;
  endedAt: string | null;
  overallScore: number | null;
  summaryJson: Record<string, unknown> | null;
  provider: string;
  messages: { role: string; content: string }[];
  feedbacks: {
    userMessage: string | null;
    feedbackJson: Record<string, unknown> | null;
    score: number | null;
  }[];
};

// ── localStorage helpers ──────────────────────────────────────────────────────

export function loadStoredUser(): GuestUser | null {
  try {
    const userId = localStorage.getItem(STORAGE_USER_ID);
    const displayName = localStorage.getItem(STORAGE_DISPLAY_NAME);
    if (userId && displayName) {
      return { userId, displayName, createdAt: "" };
    }
  } catch {
    // localStorage may be unavailable in some environments
  }
  return null;
}

export function storeUser(user: GuestUser): void {
  try {
    localStorage.setItem(STORAGE_USER_ID, user.userId);
    localStorage.setItem(STORAGE_DISPLAY_NAME, user.displayName);
  } catch {
    // ignore
  }
}

export function clearStoredUser(): void {
  try {
    localStorage.removeItem(STORAGE_USER_ID);
    localStorage.removeItem(STORAGE_DISPLAY_NAME);
  } catch {
    // ignore
  }
}

// ── API helpers ───────────────────────────────────────────────────────────────

const API_BASE = (() => {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (!raw) return "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
})();

async function historyRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const resp = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      signal: controller.signal,
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return (await resp.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

// ── Guest user API ────────────────────────────────────────────────────────────

type ApiGuestUser = {
  user_id: string;
  display_name: string;
  created_at: string;
};

export async function createGuestUser(displayName: string): Promise<GuestUser> {
  const data = await historyRequest<ApiGuestUser>("/api/users/guest", {
    method: "POST",
    body: JSON.stringify({ display_name: displayName }),
  });
  return { userId: data.user_id, displayName: data.display_name, createdAt: data.created_at };
}

export async function fetchGuestUser(userId: string): Promise<GuestUser> {
  const data = await historyRequest<ApiGuestUser>(`/api/users/${encodeURIComponent(userId)}`);
  return { userId: data.user_id, displayName: data.display_name, createdAt: data.created_at };
}

// ── History API ───────────────────────────────────────────────────────────────

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
  story_intro_zh: string | null;
  story_intro_en: string | null;
  started_at: string;
  ended_at: string | null;
  overall_score: number | null;
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
  const body = {
    user_id: payload.userId,
    session_id: payload.sessionId,
    scenario_id: payload.scenario.id,
    scenario_title: payload.scenario.title,
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
    scores: {
      ...payload.summary.scores,
      overall: payload.summary.scores["综合"],
    },
    overall_score: payload.summary.scores["综合"] ?? null,
    provider: payload.provider,
  };

  const data = await historyRequest<ApiSessionItem>("/api/history/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });

  return fromApiSessionItem(data);
}

export async function fetchSessionHistory(userId: string): Promise<HistorySessionItem[]> {
  const items = await historyRequest<ApiSessionItem[]>(
    `/api/history/sessions?user_id=${encodeURIComponent(userId)}`,
  );
  return items.map(fromApiSessionItem);
}

export async function fetchSessionDetail(sessionId: string): Promise<HistorySessionDetail> {
  const data = await historyRequest<ApiSessionDetail>(
    `/api/history/sessions/${encodeURIComponent(sessionId)}`,
  );
  return {
    sessionId: data.session_id,
    scenarioId: data.scenario_id,
    scenarioTitle: data.scenario_title,
    storyIntroZh: data.story_intro_zh,
    storyIntroEn: data.story_intro_en,
    startedAt: data.started_at,
    endedAt: data.ended_at,
    overallScore: data.overall_score,
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
