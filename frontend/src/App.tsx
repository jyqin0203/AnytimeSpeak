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
  clearStoredUser,
  createGuestUser,
  fetchSessionDetail,
  fetchSessionHistory,
  formatDateTime,
  loadStoredUser,
  providerLabel,
  saveSessionHistory,
  storeUser,
  type GuestUser,
  type HistorySessionDetail,
  type HistorySessionItem,
} from "./api/history";
import { VoiceControls } from "./components/VoiceControls";
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

  // User profile state
  const [guestUser, setGuestUser] = useState<GuestUser | null>(() => loadStoredUser());
  const [showProfileModal, setShowProfileModal] = useState(false);

  // History state
  const [historyList, setHistoryList] = useState<HistorySessionItem[]>([]);
  const [historyStatus, setHistoryStatus] = useState<AsyncState>("idle");
  const [historyDetail, setHistoryDetail] = useState<HistorySessionDetail | null>(null);
  const [historyDetailStatus, setHistoryDetailStatus] = useState<AsyncState>("idle");
  const [historySaveNote, setHistorySaveNote] = useState<string | null>(null);

  // Snapshot of session data used for saving history after summary
  const sessionSnapshotRef = useRef<{
    scenario: Scenario;
    messages: Message[];
    feedbacks: Feedback[];
    sessionId: string;
  } | null>(null);

  useEffect(() => {
    void loadScenarios();
  }, []);

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
      const conversationHistory = messages;
      const nextMessages = [...messages, userMessage];

      setMessages(nextMessages);
      setInput("");
      setSendStatus("loading");
      setFeedbackStatus("loading");
      if (recording) {
        setVoiceRecordings((current) => {
          const next = { ...current, [id]: recording.url };
          voiceRecordingsRef.current = next;
          return next;
        });
      }

      const [replyResult, feedbackResult] = await Promise.allSettled([
        sendChatMessage(selected, sessionId, conversationHistory, userMessage),
        fetchTurnFeedback(selected, sessionId, conversationHistory, userMessage),
      ]);

      const reply =
        replyResult.status === "fulfilled" ? replyResult.value.message : createLocalReply(selected, nextMessages);
      setMessages([...nextMessages, reply]);

      if (feedbackResult.status === "fulfilled") {
        setFeedback((current) => [...current, feedbackResult.value]);
        setFeedbackStatus("idle");
      } else {
        setFeedbackStatus("error");
      }

      if (replyResult.status === "fulfilled" && feedbackResult.status === "fulfilled") {
        setSource(sourceFromProvider(feedbackResult.value.provider));
        setSendStatus("idle");
        setStatusText(providerStatusText(feedbackResult.value.provider, feedbackResult.value.fallbackReason));
      } else if (replyResult.status === "fulfilled") {
        setSource(sourceFromProvider(replyResult.value.provider));
        setSendStatus("idle");
        setStatusText("AI 回复来自后端，但本轮反馈暂时不可用，可继续对话。");
      } else {
        setSource("local-fallback");
        setSendStatus("error");
        setStatusText("前端完全请求不到后端，本轮对话已使用前端本地模式继续。");
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

  const endPractice = async () => {
    const fallbackSummary = createLocalSummary(messages, feedback);
    setSummary(fallbackSummary);
    setSummaryStatus("loading");
    setHistorySaveNote(null);

    // Save a snapshot before navigating away
    const snapshotScenario = selected;
    const snapshotMessages = messages;
    const snapshotFeedbacks = feedback;
    const snapshotSessionId = sessionId ?? `local_${Date.now()}`;
    sessionSnapshotRef.current = {
      scenario: snapshotScenario,
      messages: snapshotMessages,
      feedbacks: snapshotFeedbacks,
      sessionId: snapshotSessionId,
    };

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

    // Auto-save history if user is logged in
    if (guestUser) {
      try {
        await saveSessionHistory({
          userId: guestUser.userId,
          sessionId: snapshotSessionId,
          scenario: snapshotScenario,
          messages: snapshotMessages,
          feedbacks: snapshotFeedbacks,
          summary: resolvedSummary,
          provider: resolvedProvider,
        });
      } catch {
        setHistorySaveNote("本次总结已生成，但历史记录保存失败。");
      }
    }
  };

  const openHistory = async () => {
    if (!guestUser) {
      setShowProfileModal(true);
      return;
    }
    setHistoryStatus("loading");
    setView("history");
    try {
      const items = await fetchSessionHistory(guestUser.userId);
      setHistoryList(items);
      setHistoryStatus("idle");
    } catch {
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

  const handleCreateProfile = async (displayName: string) => {
    try {
      const user = await createGuestUser(displayName);
      storeUser(user);
      setGuestUser(user);
      setShowProfileModal(false);
    } catch {
      // Backend unavailable: create a local-only profile
      const localUser: GuestUser = {
        userId: `local_${Date.now()}`,
        displayName,
        createdAt: new Date().toISOString(),
      };
      storeUser(localUser);
      setGuestUser(localUser);
      setShowProfileModal(false);
    }
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
          {guestUser ? (
            <button
              className="profile-chip"
              type="button"
              title="点击退出档案"
              onClick={() => {
                clearStoredUser();
                setGuestUser(null);
              }}
            >
              {guestUser.displayName}
            </button>
          ) : (
            <button
              className="secondary-button compact-button"
              type="button"
              onClick={() => setShowProfileModal(true)}
            >
              创建档案
            </button>
          )}
        </div>
      </header>

      {showProfileModal && (
        <ProfileModal
          onConfirm={(name) => void handleCreateProfile(name)}
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
          hasUser={!!guestUser}
          displayName={guestUser?.displayName ?? ""}
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

function ProfileModal({ onConfirm, onClose }: { onConfirm: (name: string) => void; onClose: () => void }) {
  const [name, setName] = useState("");
  const submit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (trimmed) onConfirm(trimmed);
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="创建练习档案">
      <div className="modal-card">
        <h2>创建练习档案</h2>
        <p>输入昵称即可开始记录练习历史，无需注册或密码。</p>
        <form onSubmit={submit}>
          <label htmlFor="profile-name">你的昵称</label>
          <input
            id="profile-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：Jiaying"
            maxLength={50}
            autoFocus
          />
          <div className="modal-actions">
            <button className="primary-button" type="submit" disabled={!name.trim()}>
              确认创建
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
  displayName,
  onDetail,
  onBack,
  onCreateProfile,
}: {
  items: HistorySessionItem[];
  status: AsyncState;
  hasUser: boolean;
  displayName: string;
  onDetail: (sessionId: string) => void;
  onBack: () => void;
  onCreateProfile: () => void;
}) {
  return (
    <section className="history-page page-section">
      <div className="history-header">
        <div>
          <h1>练习历史</h1>
          {hasUser && <p className="history-user">档案：{displayName}</p>}
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>
          返回首页
        </button>
      </div>

      {!hasUser && (
        <div className="history-no-user">
          <p>还没有练习档案。创建昵称后，练习记录将自动保存。</p>
          <button className="primary-button" type="button" onClick={onCreateProfile}>
            创建练习档案
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
  const latestScore = latestFeedback?.score ?? 82;
  const [speechLanguage, setSpeechLanguage] = useState("zh-CN");
  const latestAiMessage = [...messages].reverse().find((message) => message.sender === "ai");
  const latestAiText = latestAiMessage?.text ?? scenario.openingLine;
  const lastSpokenAiId = useRef<number | null>(null);
  const latestTranscriptRef = useRef("");
  const playbackRef = useRef<HTMLAudioElement | null>(null);
  const speechOutput = useSpeechOutput({ lang: "en-US", rate: 0.95, pitch: 1 });
  const voiceRecorder = useVoiceRecorder();
  const speechInput = useSpeechInput({
    lang: speechLanguage,
    interimResults: true,
    continuous: true,
    onTranscriptChange: (transcript) => {
      latestTranscriptRef.current = transcript;
      onInput(transcript);
    },
  });

  useEffect(() => {
    if (!latestAiMessage || latestAiMessage.id === lastSpokenAiId.current) return;
    lastSpokenAiId.current = latestAiMessage.id;
    speechOutput.speak(latestAiMessage.text);
  }, [latestAiMessage, speechOutput]);

  const toggleVoiceInput = () => {
    if (speechInput.isListening || speechInput.isRestarting) {
      speechInput.stopListening();
      const transcript = latestTranscriptRef.current.trim() || speechInput.transcript.trim();
      void voiceRecorder.stopRecording().then((recording) => {
        if (transcript) {
          onSendText(transcript, recording);
          speechInput.resetTranscript();
          latestTranscriptRef.current = "";
        }
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
        <VoiceControls
          input={speechInput}
          output={speechOutput}
          sampleText={latestAiText}
          language={speechLanguage}
          onLanguageChange={setSpeechLanguage}
          onToggleListening={toggleVoiceInput}
          isSending={sendStatus === "loading"}
          recorderError={voiceRecorder.error?.message ?? null}
        />
        <details className="text-fallback">
          <summary>改用文字输入</summary>
          <form className="composer" onSubmit={onSend}>
            <label htmlFor="practice-input">你的英文回答</label>
            <div>
              <input
                id="practice-input"
                value={input}
                onChange={(event) => onInput(event.target.value)}
                placeholder="例如：I finished the homepage and need help with tests."
              />
              <button className="primary-button" type="submit" disabled={sendStatus === "loading"}>
                {sendStatus === "loading" ? "发送中..." : "发送"}
              </button>
            </div>
          </form>
        </details>
      </div>

      <aside className="feedback-panel">
        <div className="coach-score">
          <span>本轮表现</span>
          <strong>{latestScore}</strong>
          <p>反馈放在旁边累积，不打断对话主线。</p>
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
            <strong>本轮反馈暂时不可用</strong>
            <p>本轮反馈生成失败，这里不会展示历史反馈。请继续对话，下一轮会重新尝试。</p>
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
                  <span>你想表达的是</span>
                  <p>{latestFeedback.userIntent}</p>
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
        <h1>{summary.scores.综合}</h1>
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
              <strong>{value}</strong>
            </div>
            <div className="score-track" aria-hidden="true">
              <span style={{ width: `${value}%` }} />
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
  if (text.includes("分析")) return "正在分析";
  if (text.includes("总结")) return "正在总结";
  return "AI 思考中";
}
