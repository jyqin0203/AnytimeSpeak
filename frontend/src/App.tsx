import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  createLocalReply,
  createLocalSummary,
  fetchScenarios,
  fetchSessionSummary,
  fetchTurnFeedback,
  localScenarios,
  sendChatMessage,
  startPracticeSession,
  type Feedback,
  type Message,
  type Scenario,
  type SessionSummary,
} from "./api/coaching";
import {
  clearPendingHistory,
  clearStoredUser,
  fetchSessionDetail,
  fetchSessionHistory,
  fetchUser,
  formatDateTime,
  HistoryRequestError,
  loadPendingHistory,
  loadStoredUser,
  loginUser,
  providerLabel,
  registerUser,
  storePendingHistory,
  saveSessionHistory,
  storeUser,
  type AuthUser,
  type HistorySessionDetail,
  type HistorySessionItem,
  type SaveHistoryPayload,
} from "./api/history";
import {
  providerBadgeText,
  providerStatusText,
  sourceFromProvider,
  sourceLabel,
  type SourceState,
} from "./providerStatus";
import { useSpeechInput, useSpeechOutput, useVoiceRecorder, type VoiceRecording } from "./speech";
import "./App.css";

type View = "home" | "scenarios" | "practice" | "summary" | "history" | "history-detail";
type AsyncState = "idle" | "loading" | "error";

const features = ["场景化练习", "AI 角色对话", "语法 / 表达反馈", "课后总结评分"];
const marketNotes = ["先明确场景目标", "对话主线不被反馈打断", "结束后沉淀分项评分与复用表达"];

function App() {
  const [view, setView] = useState<View>("home");
  const [scenarios, setScenarios] = useState<Scenario[]>(localScenarios);
  const [selected, setSelected] = useState(localScenarios[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [feedbackStatus, setFeedbackStatus] = useState<AsyncState>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [summary, setSummary] = useState<SessionSummary>(() => createLocalSummary([], []));
  const [summaryProvider, setSummaryProvider] = useState<string>("local-fallback");
  const [input, setInput] = useState("");
  const [source, setSource] = useState<SourceState>("local-fallback");
  const [scenarioStatus, setScenarioStatus] = useState<AsyncState>("loading");
  const [sendStatus, setSendStatus] = useState<AsyncState>("idle");
  const [summaryStatus, setSummaryStatus] = useState<AsyncState>("idle");
  const [statusText, setStatusText] = useState("正在连接练习服务...");
  const [voiceRecordings, setVoiceRecordings] = useState<Record<number, string>>({});
  const voiceRecordingsRef = useRef<Record<number, string>>({});
  const feedbackRequestSeqRef = useRef(0);

  // User profile state
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => loadStoredUser());
  const [showProfileModal, setShowProfileModal] = useState(false);

  // History state
  const [historyList, setHistoryList] = useState<HistorySessionItem[]>([]);
  const [historyStatus, setHistoryStatus] = useState<AsyncState>("idle");
  const [historyDetail, setHistoryDetail] = useState<HistorySessionDetail | null>(null);
  const [historyDetailStatus, setHistoryDetailStatus] = useState<AsyncState>("idle");
  const [historySaveNote, setHistorySaveNote] = useState<string | null>(null);

  // Pending save payload: always stored after endPractice so it can be
  // saved retroactively when the user creates a profile.
  const pendingHistoryRef = useRef<Omit<SaveHistoryPayload, "userId"> | null>(loadPendingHistory());

  useEffect(() => {
    void loadScenarios();
  }, []);

  useEffect(() => {
    if (!authUser) return;

    void fetchUser(authUser.userId).catch((error) => {
      if (error instanceof HistoryRequestError && error.status === 404) {
        clearStoredUser();
        setAuthUser(null);
        setHistorySaveNote("登录已失效：后端找不到当前用户。请重新登录或注册，当前练习会在登录后自动补存。");
      }
    });
  }, [authUser]);

  useEffect(
    () => () => {
      Object.values(voiceRecordingsRef.current).forEach((url) => URL.revokeObjectURL(url));
    },
    [],
  );

  const loadScenarios = async () => {
    setScenarioStatus("loading");
    setStatusText("正在连接练习服务...");

    try {
      const backendScenarios = await fetchScenarios();
      setScenarios(backendScenarios);
      setSelected((current) => backendScenarios.find((scenario) => scenario.id === current.id) ?? backendScenarios[0]);
      setSource("backend-connected");
      setScenarioStatus("idle");
      setStatusText("已连接练习服务，可以开始场景练习。");
    } catch {
      setScenarios(localScenarios);
      setSelected((current) => localScenarios.find((scenario) => scenario.id === current.id) ?? localScenarios[0]);
      setSource("local-fallback");
      setScenarioStatus("error");
      setStatusText("练习服务暂不可用，已切换到本地练习模式。");
    }
  };

  const start = (scenario: Scenario) => {
    setSelected(scenario);
    setMessages([{ id: 1, sender: "ai", text: scenario.openingLine }]);
    setFeedback([]);
    setFeedbackStatus("idle");
    setSessionId(null);
    setSummary(createLocalSummary([], []));
    setSummaryProvider("local-fallback");
    Object.values(voiceRecordingsRef.current).forEach((url) => URL.revokeObjectURL(url));
    voiceRecordingsRef.current = {};
    setVoiceRecordings({});
    setSendStatus("idle");
    setSummaryStatus("idle");
    setHistorySaveNote(null);
    setInput("");
    setView("practice");
    void startPracticeSession(scenario)
      .then((session) => {
        setSessionId(session.sessionId);
        setSelected((current) => ({
          ...current,
          storySeedId: session.storySeedId,
          storyIntroZh: session.storyIntroZh,
          storyIntroEn: session.storyIntroEn,
          openingLine: session.openingMessage,
        }));
        setMessages([{ id: 1, sender: "ai", text: session.openingMessage }]);
        setSource("backend-connected");
        setStatusText("已根据本轮场景故事开始练习。");
      })
      .catch(() => {
        setSource("local-fallback");
        setStatusText("练习会话暂时连不上后端，已使用本地模式继续。");
      });
  };

  const sendText = useCallback(
    async (rawText: string, recording?: VoiceRecording | null) => {
      const text = rawText.trim();
      if (!text || sendStatus === "loading") return;

      const id = Date.now();
      const userMessage: Message = { id, sender: "user", text };
      const loadingMessage: Message = { id: id + 1, sender: "ai", text: "AI 正在回复...", isLoading: true };
      const conversationHistory = messages;
      const nextMessages = [...messages, userMessage];
      const loadingMessages = [...nextMessages, loadingMessage];
      const feedbackRequestSeq = feedbackRequestSeqRef.current + 1;
      feedbackRequestSeqRef.current = feedbackRequestSeq;

      setMessages(loadingMessages);
      setInput("");
      setSendStatus("loading");
      setFeedbackStatus("loading");
      setStatusText("AI 正在回复...");
      if (recording) {
        setVoiceRecordings((current) => {
          const next = { ...current, [id]: recording.url };
          voiceRecordingsRef.current = next;
          return next;
        });
      }

      void fetchTurnFeedback(selected, sessionId, conversationHistory, userMessage)
        .then((turnFeedback) => {
          setFeedback((current) =>
            [...current.filter((item) => item.id !== turnFeedback.id), turnFeedback].sort((a, b) => a.id - b.id),
          );
          if (feedbackRequestSeqRef.current === feedbackRequestSeq) {
            setFeedbackStatus("idle");
          }
        })
        .catch(() => {
          if (feedbackRequestSeqRef.current === feedbackRequestSeq) {
            setFeedbackStatus("error");
          }
        });

      try {
        const replyResult = await sendChatMessage(selected, sessionId, conversationHistory, userMessage);
        const reply = { ...replyResult.message, id: loadingMessage.id };
        setMessages([...nextMessages, reply]);
        setSource(sourceFromProvider(replyResult.provider));
        setSendStatus("idle");
        setStatusText(providerStatusText(replyResult.provider, replyResult.fallbackReason));
      } catch {
        const fallbackReply = { ...createLocalReply(selected, nextMessages), id: loadingMessage.id };
        setMessages([...nextMessages, fallbackReply]);
        setSource("local-fallback");
        setSendStatus("error");
        setStatusText("当前使用本地 fallback 回复。");
      }
    },
    [messages, selected, sendStatus, sessionId],
  );

  const send = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendText(input);
  };

  const submitVoiceText = (text: string, recording?: VoiceRecording | null) => {
    if (!text || sendStatus === "loading") return;
    void sendText(text, recording);
  };

  const trySaveHistory = async (user: AuthUser, payload: Omit<SaveHistoryPayload, "userId">) => {
    try {
      await saveSessionHistory({ ...payload, userId: user.userId });
      pendingHistoryRef.current = null;
      clearPendingHistory();
      const items = await fetchSessionHistory(user.userId);
      setHistoryList(items);
      setHistoryStatus("idle");
    } catch (error) {
      if (error instanceof HistoryRequestError && error.status === 404) {
        clearStoredUser();
        setAuthUser(null);
        setShowProfileModal(true);
        storePendingHistory(payload);
        setHistorySaveNote("本次总结已生成，但当前登录已失效。请重新登录或注册，系统会自动补存这次练习。");
        return;
      }

      storePendingHistory(payload);
      setHistorySaveNote("本次总结已生成，但历史记录保存失败。请确认后端服务正在运行，然后打开练习历史重试自动补存。");
    }
  };

  const endPractice = async () => {
    const fallbackSummary = createLocalSummary(messages, feedback);
    setSummary(fallbackSummary);
    setSummaryStatus("loading");
    setHistorySaveNote(null);

    const snapshotScenario = selected;
    const snapshotMessages = [...messages];
    const snapshotFeedbacks = [...feedback];
    const snapshotSessionId = sessionId ?? `local_${Date.now()}`;

    setView("summary");

    let resolvedSummary = fallbackSummary;
    let resolvedProvider = "local-fallback";

    try {
      const backendSummary = await fetchSessionSummary(selected, messages);
      setSummary(backendSummary);
      setSummaryProvider(backendSummary.provider);
      setSource(sourceFromProvider(backendSummary.provider));
      setSummaryStatus("idle");
      setStatusText(providerStatusText(backendSummary.provider, backendSummary.fallbackReason));
      resolvedSummary = backendSummary;
      resolvedProvider = backendSummary.provider;
    } catch {
      setSummary(fallbackSummary);
      setSummaryProvider("local-fallback");
      setSource("local-fallback");
      setSummaryStatus("error");
      setStatusText("前端完全请求不到后端，已展示前端本地模式生成的总结。");
    }

    // Always store the pending payload so it can be saved later if the user
    // creates a profile after viewing the summary.
    const pendingPayload: Omit<SaveHistoryPayload, "userId"> = {
      sessionId: snapshotSessionId,
      scenario: snapshotScenario,
      messages: snapshotMessages,
      feedbacks: snapshotFeedbacks,
      summary: resolvedSummary,
      provider: resolvedProvider,
    };
    pendingHistoryRef.current = pendingPayload;
    storePendingHistory(pendingPayload);

    if (authUser) {
      await trySaveHistory(authUser, pendingPayload);
    } else {
      setHistorySaveNote("登录或注册后即可保存本次练习记录。点击右上角「登录 / 注册」。");
    }
  };

  const openHistory = async () => {
    if (!authUser) {
      setShowProfileModal(true);
      return;
    }
    setHistoryStatus("loading");
    setView("history");
    try {
      const pending = pendingHistoryRef.current ?? loadPendingHistory();
      if (pending) {
        pendingHistoryRef.current = pending;
        await trySaveHistory(authUser, pending);
      }
      const items = await fetchSessionHistory(authUser.userId);
      setHistoryList(items);
      setHistoryStatus("idle");
    } catch (error) {
      if (error instanceof HistoryRequestError && error.status === 404) {
        clearStoredUser();
        setAuthUser(null);
        setShowProfileModal(true);
        setHistorySaveNote("登录已失效，请重新登录后查看历史。");
      }
      setHistoryList([]);
      setHistoryStatus("error");
    }
  };

  const openHistoryDetail = async (sessionId: string) => {
    setHistoryDetailStatus("loading");
    setView("history-detail");
    try {
      const detail = await fetchSessionDetail(sessionId);
      setHistoryDetail(detail);
      setHistoryDetailStatus("idle");
    } catch {
      setHistoryDetail(null);
      setHistoryDetailStatus("error");
    }
  };

  const handleAuth = async (mode: "login" | "register", username: string, password: string): Promise<string | null> => {
    let nextUser: AuthUser | null = null;
    try {
      const user = mode === "register" ? await registerUser(username, password) : await loginUser(username, password);
      storeUser(user);
      setAuthUser(user);
      setShowProfileModal(false);
      nextUser = user;
    } catch {
      const message = mode === "register" ? "注册失败：用户名可能已存在，或后端服务暂不可用。" : "登录失败：请检查用户名、密码，或确认后端服务正在运行。";
      setHistorySaveNote(message);
      return message;
    }

    const pending = pendingHistoryRef.current ?? loadPendingHistory();
    if (nextUser && pending) {
      try {
        await saveSessionHistory({ ...pending, userId: nextUser.userId });
        pendingHistoryRef.current = null;
        clearPendingHistory();
        setHistorySaveNote(null);
      } catch {
        pendingHistoryRef.current = pending;
        storePendingHistory(pending);
        setHistorySaveNote("登录成功，但本次历史记录保存失败。请稍后再试。");
      }
    }
    return null;
  };

  return (
    <main className="app">
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => setView("home")}>
          <span className="brand-mark">AS</span>
          <span>
            AnytimeSpeak
            <small>AI 英语口语教练</small>
          </span>
        </button>
        <nav aria-label="练习流程">
          <button className={view === "home" ? "active" : ""} type="button" onClick={() => setView("home")}>
            首页
          </button>
          <button className={view === "scenarios" ? "active" : ""} type="button" onClick={() => setView("scenarios")}>
            选场景
          </button>
          <button className={view === "practice" ? "active" : ""} type="button" onClick={() => start(selected)}>
            开始练习
          </button>
        </nav>
        <div className="topbar-profile">
          <button
            className="history-button secondary-button compact-button"
            type="button"
            onClick={() => void openHistory()}
          >
            练习历史
          </button>
          {authUser ? (
            <button
              className="profile-chip"
              type="button"
              title="退出登录"
              onClick={() => {
                clearStoredUser();
                setAuthUser(null);
              }}
            >
              {authUser.username}
            </button>
          ) : (
            <button
              className="secondary-button compact-button"
              type="button"
              onClick={() => setShowProfileModal(true)}
            >
              登录 / 注册
            </button>
          )}
        </div>
      </header>

      {showProfileModal && (
        <ProfileModal
          onConfirm={handleAuth}
          onClose={() => setShowProfileModal(false)}
        />
      )}

      {view === "home" && <Home onStart={() => setView("scenarios")} source={source} statusText={statusText} />}
      {view === "scenarios" && (
        <Scenarios
          selected={selected}
          scenarios={scenarios}
          status={scenarioStatus}
          source={source}
          statusText={statusText}
          onRetry={loadScenarios}
          onSelect={setSelected}
          onStart={start}
        />
      )}
      {view === "practice" && (
        <Practice
          scenario={selected}
          messages={messages}
          voiceRecordings={voiceRecordings}
          feedback={feedback}
          feedbackStatus={feedbackStatus}
          sessionId={sessionId}
          input={input}
          source={source}
          statusText={statusText}
          sendStatus={sendStatus}
          onInput={setInput}
          onSend={send}
          onSendText={submitVoiceText}
          onEnd={endPractice}
          onReset={() => setView("scenarios")}
        />
      )}
      {view === "summary" && (
        <Summary
          scenario={selected}
          summary={summary}
          status={summaryStatus}
          source={source}
          statusText={statusText}
          historySaveNote={historySaveNote}
          onAgain={() => start(selected)}
          onChoose={() => setView("scenarios")}
        />
      )}
      {view === "history" && (
        <HistoryList
          items={historyList}
          status={historyStatus}
          hasUser={!!authUser}
          username={authUser?.username ?? ""}
          onDetail={openHistoryDetail}
          onBack={() => setView("home")}
          onCreateProfile={() => setShowProfileModal(true)}
        />
      )}
      {view === "history-detail" && (
        <HistoryDetailView
          detail={historyDetail}
          status={historyDetailStatus}
          onBack={() => void openHistory()}
        />
      )}
    </main>
  );
}

// ── ProfileModal ──────────────────────────────────────────────────────────────

function ProfileModal({
  onConfirm,
  onClose,
}: {
  onConfirm: (mode: "login" | "register", username: string, password: string) => Promise<string | null>;
  onClose: () => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting">("idle");
  const [error, setError] = useState<string | null>(null);
  const submit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed || password.length < 6 || status === "submitting") return;

    setStatus("submitting");
    setError(null);
    void onConfirm(mode, trimmed, password)
      .then((message) => {
        if (message) setError(message);
      })
      .catch(() => {
        setError("请求失败：请确认后端服务正在运行。");
      })
      .finally(() => setStatus("idle"));
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="用户登录或注册">
      <div className="modal-card">
        <h2>{mode === "login" ? "登录练习档案" : "创建练习档案"}</h2>
        <p>使用用户名和密码保存练习历史。退出后重新登录，也可以继续查看自己的记录。</p>
        <div className="auth-mode-row">
          <button
            className={mode === "login" ? "active" : ""}
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
          >
            登录
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
          >
            注册
          </button>
        </div>
        <form onSubmit={submit}>
          <label htmlFor="profile-username">用户名</label>
          <input
            id="profile-username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="例如：jiaying"
            maxLength={50}
            autoFocus
          />
          <label htmlFor="profile-password">密码</label>
          <input
            id="profile-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少 6 位"
            type="password"
            maxLength={128}
          />
          {error && <p className="modal-error">{error}</p>}
          <div className="modal-actions">
            <button
              className="primary-button"
              type="submit"
              disabled={!username.trim() || password.length < 6 || status === "submitting"}
            >
              {status === "submitting" ? "处理中..." : mode === "login" ? "登录" : "注册并登录"}
            </button>
            <button className="secondary-button" type="button" onClick={onClose}>
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── HistoryList ───────────────────────────────────────────────────────────────

function HistoryList({
  items,
  status,
  hasUser,
  username,
  onDetail,
  onBack,
  onCreateProfile,
}: {
  items: HistorySessionItem[];
  status: AsyncState;
  hasUser: boolean;
  username: string;
  onDetail: (sessionId: string) => void;
  onBack: () => void;
  onCreateProfile: () => void;
}) {
  return (
    <section className="history-page page-section">
      <div className="history-header">
        <div>
          <h1>练习历史</h1>
          {hasUser && <p className="history-user">用户：{username}</p>}
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>
          返回首页
        </button>
      </div>

      {!hasUser && (
        <div className="history-no-user">
          <p>还没有练习档案。创建昵称后，练习记录将自动保存。</p>
          <button className="primary-button" type="button" onClick={onCreateProfile}>
            登录 / 注册
          </button>
        </div>
      )}

      {hasUser && status === "loading" && (
        <div className="empty-state">
          <strong>正在加载练习历史...</strong>
        </div>
      )}

      {hasUser && status === "error" && (
        <div className="empty-state error">
          <strong>历史记录加载失败</strong>
          <p>请检查后端是否运行，或稍后再试。</p>
        </div>
      )}

      {hasUser && status === "idle" && items.length === 0 && (
        <div className="empty-state">
          <strong>还没有练习记录</strong>
          <p>完成一次练习并结束后，记录会自动保存到这里。</p>
        </div>
      )}

      {hasUser && status === "idle" && items.length > 0 && (
        <div className="history-list">
          {items.map((item) => (
            <button
              className="history-item-card"
              key={item.sessionId}
              type="button"
              onClick={() => onDetail(item.sessionId)}
            >
              <div className="history-item-top">
                <strong>{item.scenarioTitle}</strong>
                <span className={`provider-badge ${item.provider === "llm" ? "llm" : "fallback"}`}>
                  {providerLabel(item.provider)}
                </span>
              </div>
              <div className="history-item-meta">
                <span>{formatDateTime(item.startedAt)}</span>
                {item.overallScore !== null && (
                  <span className="history-score">综合 {item.overallScore}</span>
                )}
              </div>
              {item.summaryPreview && (
                <p className="history-preview">{item.summaryPreview}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

// ── HistoryDetailView ─────────────────────────────────────────────────────────

function HistoryDetailView({
  detail,
  status,
  onBack,
}: {
  detail: HistorySessionDetail | null;
  status: AsyncState;
  onBack: () => void;
}) {
  if (status === "loading") {
    return (
      <section className="history-page page-section">
        <div className="empty-state">
          <strong>正在加载练习详情...</strong>
        </div>
      </section>
    );
  }

  if (status === "error" || !detail) {
    return (
      <section className="history-page page-section">
        <div className="empty-state error">
          <strong>加载失败</strong>
          <p>无法获取该条练习记录，请稍后再试。</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>
          返回历史列表
        </button>
      </section>
    );
  }

  const summary = detail.summaryJson ?? {};
  const strengths = (summary["strengths"] as string[] | undefined) ?? [];
  const repeatedIssues = (summary["repeated_issues"] as string[] | undefined) ?? [];
  const betterExpressions = (summary["better_expressions"] as string[] | undefined) ?? [];
  const scores = (summary["scores"] as Record<string, number> | undefined) ?? {};
  const overallText = (summary["summary"] as string | undefined) ?? "";

  return (
    <section className="history-page page-section">
      <div className="history-header">
        <div>
          <h1>{detail.scenarioTitle} · 练习详情</h1>
          <p className="history-user">
            {formatDateTime(detail.startedAt)}
            {detail.overallScore !== null && ` · 综合 ${detail.overallScore}`}
            <span className={`provider-badge ${detail.provider === "llm" ? "llm" : "fallback"}`} style={{ marginLeft: "0.5rem" }}>
              {providerLabel(detail.provider)}
            </span>
          </p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>
          返回历史列表
        </button>
      </div>

      {(detail.storyIntroZh || detail.storyIntroEn) && (
        <div className="history-story">
          <span>情境前言</span>
          {detail.storyIntroZh && <p>{detail.storyIntroZh}</p>}
          {detail.storyIntroEn && <p className="story-intro-en">{detail.storyIntroEn}</p>}
        </div>
      )}

      {overallText && (
        <div className="history-section">
          <h2>总体评价</h2>
          <p>{overallText}</p>
        </div>
      )}

      {Object.keys(scores).length > 0 && (
        <div className="history-section">
          <h2>评分</h2>
          <div className="score-board">
            {Object.entries(scores).map(([label, value]) => (
              <article className="score-row" key={label}>
                <div>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
                <div className="score-track" aria-hidden="true">
                  <span style={{ width: `${value}%` }} />
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {detail.messages.length > 0 && (
        <div className="history-section">
          <h2>对话记录</h2>
          <div className="history-messages">
            {detail.messages.map((msg, i) => (
              <div className={`message-bubble ${msg.role === "assistant" ? "ai" : "user"}`} key={i}>
                <div className="message-meta">
                  <span>{msg.role === "assistant" ? "AI" : "你"}</span>
                </div>
                <p>{msg.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {detail.feedbacks.length > 0 && (
        <div className="history-section">
          <h2>即时反馈</h2>
          <div className="history-feedbacks">
            {detail.feedbacks.map((fb, i) => (
              <div className="feedback-card" key={i}>
                {fb.score !== null && <div className="score-pill">{fb.score}</div>}
                {fb.userMessage && (
                  <div>
                    <span>你说的是</span>
                    <p>{fb.userMessage}</p>
                  </div>
                )}
                {fb.feedbackJson && (fb.feedbackJson["issue"] as string | undefined) && (
                  <div>
                    <span>主要问题</span>
                    <p>{fb.feedbackJson["issue"] as string}</p>
                  </div>
                )}
                {fb.feedbackJson && (fb.feedbackJson["recommended_english"] as string | undefined) && (
                  <div>
                    <span>推荐英文表达</span>
                    <p className="english-suggestion">{fb.feedbackJson["recommended_english"] as string}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {(strengths.length > 0 || repeatedIssues.length > 0 || betterExpressions.length > 0) && (
        <div className="summary-columns">
          {strengths.length > 0 && <SummaryList title="优势" items={strengths} />}
          {repeatedIssues.length > 0 && <SummaryList title="常见问题" items={repeatedIssues} />}
          {betterExpressions.length > 0 && <SummaryList title="建议复用表达" items={betterExpressions} />}
        </div>
      )}
    </section>
  );
}

// ── Existing views ────────────────────────────────────────────────────────────

function Home({ onStart, source, statusText }: { onStart: () => void; source: SourceState; statusText: string }) {
  return (
    <section className="landing-grid page-section">
      <div className="hero-copy">
        <span className="eyebrow">{sourceLabel(source)}</span>
        <h1>随时开口练英语</h1>
        <p className="product-positioning">AnytimeSpeak · AI English Speaking Coach</p>
        <p className="hero-description">从真实场景进入对话，边练边看语法和表达建议，结束后获得一份清晰的口语能力总结。</p>
        <div className="hero-actions">
          <button className="primary-button" type="button" onClick={onStart}>
            开始练习
          </button>
          <span>{statusText}</span>
        </div>
      </div>

      <div className="hero-panel">
        <div className="hero-panel-header">
          <span>今日练习预览</span>
        </div>
        <div className="preview-chat">
          <p className="preview-message ai">Could you briefly introduce yourself?</p>
          <p className="preview-message user">I am a frontend developer and I enjoy building useful products.</p>
          <div className="preview-feedback">
            <strong>更自然的表达</strong>
            <span>I have experience building user-focused web products.</span>
          </div>
        </div>
        <div className="mini-score-grid">
          <span>语法 86</span>
          <span>表达 88</span>
          <span>完成度 90</span>
        </div>
      </div>

      <div className="feature-strip">
        {features.map((feature) => (
          <article className="feature-item" key={feature}>
            <span />
            <p>{feature}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function Scenarios({
  selected,
  scenarios,
  status,
  source,
  statusText,
  onRetry,
  onSelect,
  onStart,
}: {
  selected: Scenario;
  scenarios: Scenario[];
  status: AsyncState;
  source: SourceState;
  statusText: string;
  onRetry: () => void;
  onSelect: (scenario: Scenario) => void;
  onStart: (scenario: Scenario) => void;
}) {
  return (
    <section className="page-section scenario-page">
      <aside className="learning-rail">
        <span className="eyebrow">学习路径</span>
        <h2>先选一个真实场景</h2>
        <p>参考口语练习产品的常见结构：先展示目标、角色、难度和时长，再进入对话。</p>
        <div className="streak-card">
          <strong>3</strong>
          <span>今日建议轮次</span>
        </div>
        <ul>
          {marketNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </aside>

      <div>
        <div className="section-heading">
          <h2>选择练习场景</h2>
          <p>每个卡片都标出 AI 角色、练习目标和重点表达，方便 demo 时快速进入主题。</p>
        </div>
        <StatusBanner status={status} source={source} text={statusText} onRetry={onRetry} />
        <div className="scenario-grid">
          {scenarios.map((scenario) => (
            <button
              className={`scenario-card ${selected.id === scenario.id ? "selected" : ""}`}
              key={scenario.id}
              type="button"
              onClick={() => onSelect(scenario)}
            >
              <div className="scenario-card-top">
                <span className="difficulty">{scenario.level}</span>
                <span>{scenario.duration}</span>
              </div>
              <h3>{scenario.title}</h3>
              <p>{scenario.description}</p>
              <p className="scenario-story">{scenario.storyIntroZh}</p>
              <p className="scenario-story-en">{scenario.storyIntroEn}</p>
              <TagList items={scenario.focus} />
              <dl>
                <div>
                  <dt>AI 角色</dt>
                  <dd>{scenario.aiRole}</dd>
                </div>
                <div>
                  <dt>练习目标</dt>
                  <dd>{scenario.goal}</dd>
                </div>
              </dl>
            </button>
          ))}
        </div>
        <div className="scenario-action">
          <div>
            <span>当前选择</span>
            <strong>{selected.title}</strong>
          </div>
          <button className="primary-button" type="button" onClick={() => onStart(selected)}>
            进入 {selected.title}
          </button>
        </div>
      </div>
    </section>
  );
}

function Practice({
  scenario,
  messages,
  voiceRecordings,
  feedback,
  feedbackStatus,
  sessionId,
  input,
  source,
  statusText,
  sendStatus,
  onInput,
  onSend,
  onSendText,
  onEnd,
  onReset,
}: {
  scenario: Scenario;
  messages: Message[];
  voiceRecordings: Record<number, string>;
  feedback: Feedback[];
  feedbackStatus: AsyncState;
  sessionId: string | null;
  input: string;
  source: SourceState;
  statusText: string;
  sendStatus: AsyncState;
  onInput: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
  onSendText: (value: string, recording?: VoiceRecording | null) => void;
  onEnd: () => void;
  onReset: () => void;
}) {
  const turns = messages.filter((message) => message.sender === "user").length;
  const latestFeedback = feedback[feedback.length - 1];
  const latestScore = latestFeedback?.score ?? null;
  const latestAiMessage = [...messages].reverse().find((message) => message.sender === "ai");
  const latestAiText = latestAiMessage?.text ?? scenario.openingLine;
  const lastSpokenAiKey = useRef<string | null>(null);
  const latestTranscriptRef = useRef("");
  const playbackRef = useRef<HTMLAudioElement | null>(null);
  const speechOutput = useSpeechOutput({ lang: "en-US", rate: 0.95, pitch: 1 });
  const voiceRecorder = useVoiceRecorder();
  const speechInput = useSpeechInput({
    lang: "en-US",
    interimResults: true,
    continuous: true,
    onTranscriptChange: (transcript) => {
      latestTranscriptRef.current = transcript;
      onInput(transcript);
    },
  });
  const isRecording = speechInput.isListening || speechInput.isRestarting;

  useEffect(() => {
    if (!latestAiMessage || latestAiMessage.isLoading) return;
    const spokenKey = `${latestAiMessage.id}:${latestAiMessage.text}`;
    if (spokenKey === lastSpokenAiKey.current) return;
    lastSpokenAiKey.current = spokenKey;
    speechOutput.speak(latestAiMessage.text);
  }, [latestAiMessage, speechOutput]);

  const toggleVoiceInput = () => {
    if (speechInput.isListening || speechInput.isRestarting) {
      speechInput.stopListening();
      const transcript = latestTranscriptRef.current.trim() || speechInput.transcript.trim();
      void voiceRecorder
        .stopRecording()
        .then((recording) => {
          if (transcript) {
            onSendText(transcript, recording);
          }
        })
        .finally(() => {
          speechInput.resetTranscript();
          latestTranscriptRef.current = "";
          onInput("");
        });
      return;
    }

    latestTranscriptRef.current = "";
    speechInput.resetTranscript();
    void voiceRecorder.startRecording().finally(() => {
      speechInput.startListening();
    });
  };

  const playMessageAudio = (message: Message) => {
    const recordingUrl = message.sender === "user" ? voiceRecordings[message.id] : undefined;

    if (recordingUrl) {
      speechOutput.stopSpeaking();
      playbackRef.current?.pause();
      playbackRef.current = new Audio(recordingUrl);
      void playbackRef.current.play();
      return;
    }

    speechOutput.speak(message.text);
  };

  useEffect(
    () => () => {
      playbackRef.current?.pause();
    },
    [],
  );

  return (
    <section className="practice-shell page-section">
      <aside className="practice-context">
        <span className="difficulty">{scenario.level}</span>
        <h2>{scenario.title}</h2>
        <p>{scenario.description}</p>
        <div className="story-intro">
          <span>情境前言</span>
          <p>{scenario.storyIntroZh}</p>
          <p className="story-intro-en">{scenario.storyIntroEn}</p>
        </div>
        <dl>
          <div>
            <dt>AI 角色</dt>
            <dd>{scenario.aiRole}</dd>
          </div>
          <div>
            <dt>你的角色</dt>
            <dd>{scenario.userRole}</dd>
          </div>
          <div>
            <dt>练习目标</dt>
            <dd>{scenario.goal}</dd>
          </div>
        </dl>
        <div className="useful-expression-box">
          <span>可复用表达</span>
          <ul>
            {scenario.usefulExpressions.map((expression) => (
              <li key={expression}>{expression}</li>
            ))}
          </ul>
        </div>
        <TagList items={scenario.focus} />
        <button className="secondary-button" type="button" onClick={onReset}>
          更换场景
        </button>
      </aside>

      <div className="conversation-panel">
        <div className="panel-title">
          <div>
            <h2>对话练习</h2>
            <p>{sessionId ? `会话编号：${sessionId}` : "正在准备本轮练习会话，练习服务不可用时将自动切换到本地模式。"}</p>
          </div>
          <button className="danger-button" type="button" onClick={onEnd} disabled={sendStatus === "loading"}>
            {sendStatus === "loading" ? "请稍等" : "结束练习"}
          </button>
        </div>
        <StatusBanner status={sendStatus} source={source} text={statusText} />
        <div className="practice-progress">
          <span>当前场景：{scenario.title}</span>
          <div aria-hidden="true">
            <span style={{ width: `${Math.min(100, messages.length * 14)}%` }} />
          </div>
          <strong>{turns} 轮</strong>
        </div>
        <div className="message-list" aria-live="polite">
          {messages.map((message) => {
            const hasRecording = message.sender === "user" && Boolean(voiceRecordings[message.id]);

            return (
              <article className={`message-bubble ${message.sender}`} key={message.id}>
                <div className="message-meta">
                  <span>{message.sender === "ai" ? scenario.aiRole : "你"}</span>
                  <button
                    className="read-aloud-button"
                    type="button"
                    onClick={() => playMessageAudio(message)}
                    disabled={!hasRecording && (!speechOutput.isSupported || speechOutput.isSpeaking)}
                  >
                    {message.sender === "ai" ? "重播" : hasRecording ? "录音" : "朗读"}
                  </button>
                </div>
                <p>{message.text}</p>
              </article>
            );
          })}
        </div>
        <form className="chat-composer" onSubmit={onSend}>
          <input
            id="practice-input"
            className="chat-input"
            value={input}
            onChange={(e) => onInput(e.target.value)}
            placeholder={isRecording ? "聆听中，再点一次停止并发送..." : "输入回答，或点击右侧麦克风说话"}
            disabled={sendStatus === "loading"}
            autoComplete="off"
          />
          <button
            className={`mic-btn${isRecording ? " recording" : ""}`}
            type="button"
            onClick={toggleVoiceInput}
            disabled={!speechInput.isSupported || sendStatus === "loading"}
            title={isRecording ? "停止录音并发送" : "开始语音输入"}
            aria-label={isRecording ? "停止录音并发送" : "开始语音输入"}
          >
            <span className="microphone-icon" aria-hidden="true"><span /></span>
          </button>
          <button className="primary-button" type="submit" disabled={sendStatus === "loading" || (!input.trim() && !isRecording)}>
            {sendStatus === "loading" ? "..." : "发送"}
          </button>
        </form>
      </div>

      <aside className="feedback-panel">
        <div className="coach-score">
          <span>本轮</span>
          <strong>{latestScore !== null ? latestScore : "—"}</strong>
        </div>
        <div className="panel-title compact">
          <h2>即时反馈</h2>
          <p>只展示最新一轮：你刚才说的是、推荐英文表达、原因说明和本轮评分。</p>
        </div>
        {feedbackStatus === "loading" ? (
          <div className="empty-state">
            <strong>正在分析你的表达...</strong>
            <p>正在结合当前场景故事生成本轮反馈，请稍候。</p>
          </div>
        ) : feedbackStatus === "error" ? (
          <div className="empty-state error">
            <strong>本轮表达反馈生成失败，可以继续练习。</strong>
            <p>这里不会展示历史反馈，下一轮发送后会重新尝试分析你的表达。</p>
          </div>
        ) : feedback.length === 0 ? (
          <div className="empty-state">
            <strong>还没有反馈</strong>
            <p>发送一句后，这里只展示最新一轮的推荐英文、问题原因和更自然表达。</p>
          </div>
        ) : (
          <div className="feedback-list">
            {latestFeedback && (
              <article className="feedback-card" key={latestFeedback.id}>
                <div className="score-pill">{latestFeedback.score}</div>
                <div>
                  <span>你刚才说的是</span>
                  <p>{latestFeedback.whatYouSaid}</p>
                </div>
                <div>
                  <span>推荐英文表达</span>
                  <p className="english-suggestion">{latestFeedback.recommendedEnglish}</p>
                </div>
                <div>
                  <span>为什么这样更自然</span>
                  <p>主要问题：{latestFeedback.issue}</p>
                  <p>为什么：{latestFeedback.why}</p>
                </div>
                <div>
                  <span>更自然的说法</span>
                  <p className="english-suggestion">{latestFeedback.moreNaturalOption}</p>
                </div>
                <div className="score-breakdown">
                  <div className="score-breakdown-head">
                    <span>本轮评分</span>
                    <span className={`provider-badge ${latestFeedback.provider === "llm" ? "llm" : "fallback"}`}>
                      {providerBadgeText(latestFeedback.provider)}
                    </span>
                  </div>
                  <div className="score-breakdown-grid">
                    {Object.entries(latestFeedback.scoreBreakdown).map(([label, value]) => (
                      <span key={label}>
                        {label} {value}
                      </span>
                    ))}
                  </div>
                </div>
              </article>
            )}
          </div>
        )}
      </aside>
    </section>
  );
}

function Summary({
  scenario,
  summary,
  status,
  source,
  statusText,
  historySaveNote,
  onAgain,
  onChoose,
}: {
  scenario: Scenario;
  summary: SessionSummary;
  status: AsyncState;
  source: SourceState;
  statusText: string;
  historySaveNote: string | null;
  onAgain: () => void;
  onChoose: () => void;
}) {
  return (
    <section className="summary-layout page-section">
      <div className="summary-hero">
        <span>{scenario.title} · 课后总结</span>
        <h1>{status === "loading" ? "—" : summary.scores.综合}</h1>
        <p className="summary-provider-line">
          总体评价：{status === "loading" ? "正在生成课后总结和评分..." : summary.overallPerformance}
          <span className={`provider-badge ${summary.provider === "llm" ? "llm" : "fallback"}`}>
            {providerBadgeText(summary.provider)}
          </span>
        </p>
        <StatusBanner status={status} source={source} text={statusText} />
        {historySaveNote && (
          <p className="history-save-note">{historySaveNote}</p>
        )}
        <div className="summary-actions">
          <button className="primary-button" type="button" onClick={onAgain}>
            再练一次
          </button>
          <button className="secondary-button" type="button" onClick={onChoose}>
            选择新场景
          </button>
        </div>
      </div>

      <div className="score-board">
        {Object.entries(summary.scores).map(([label, value]) => (
          <article className="score-row" key={label}>
            <div>
              <span>{label}</span>
              <strong>{status === "loading" ? "—" : value}</strong>
            </div>
            <div className="score-track" aria-hidden="true">
              <span style={{ width: status === "loading" ? "0%" : `${value}%` }} />
            </div>
          </article>
        ))}
      </div>

      <div className="summary-columns">
        <SummaryList title="优势" items={summary.strengths} />
        <SummaryList title="常见问题" items={summary.repeatedIssues} />
        <SummaryList title="建议复用表达" items={summary.betterExpressions} />
      </div>
    </section>
  );
}

function StatusBanner({
  status,
  source,
  text,
  onRetry,
}: {
  status: AsyncState;
  source: SourceState;
  text: string;
  onRetry?: () => void;
}) {
  return (
    <div className={`status-banner ${status} ${source}`} role="status">
      <span>{status === "loading" ? loadingLabel(text) : sourceLabel(source)}</span>
      <p>{text}</p>
      {onRetry && (
        <button className="secondary-button compact-button" type="button" onClick={onRetry}>
          重试
        </button>
      )}
    </div>
  );
}

function TagList({ items }: { items: string[] }) {
  return (
    <div className="focus-tags">
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

function SummaryList({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="summary-card">
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

export default App;

function loadingLabel(text: string): string {
  if (text.includes("回复")) return "AI 正在回复";
  if (text.includes("分析")) return "正在分析";
  if (text.includes("总结")) return "正在总结";
  return "AI 思考中";
}
