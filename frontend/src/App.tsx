import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  createLocalFeedback,
  createLocalReply,
  createLocalSummary,
  fetchScenarios,
  fetchSessionSummary,
  fetchTurnFeedback,
  localScenarios,
  sendChatMessage,
  type Feedback,
  type Message,
  type Scenario,
  type SessionSummary,
} from "./api/coaching";
import { VoiceControls } from "./components/VoiceControls";
import { useSpeechInput, useSpeechOutput } from "./speech";
import "./App.css";

type View = "home" | "scenarios" | "practice" | "summary";
type SourceState = "backend" | "fallback";
type AsyncState = "idle" | "loading" | "error";

const features = ["场景化练习", "AI 角色对话", "语法 / 表达反馈", "课后总结评分"];
const marketNotes = ["先明确场景目标", "对话主线不被反馈打断", "结束后沉淀分项评分与复用表达"];

function App() {
  const [view, setView] = useState<View>("home");
  const [scenarios, setScenarios] = useState<Scenario[]>(localScenarios);
  const [selected, setSelected] = useState(localScenarios[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [summary, setSummary] = useState<SessionSummary>(() => createLocalSummary([], []));
  const [input, setInput] = useState("");
  const [source, setSource] = useState<SourceState>("fallback");
  const [scenarioStatus, setScenarioStatus] = useState<AsyncState>("loading");
  const [sendStatus, setSendStatus] = useState<AsyncState>("idle");
  const [summaryStatus, setSummaryStatus] = useState<AsyncState>("idle");
  const [statusText, setStatusText] = useState("正在连接后端 mock coaching APIs...");

  useEffect(() => {
    void loadScenarios();
  }, []);

  const loadScenarios = async () => {
    setScenarioStatus("loading");
    setStatusText("正在连接后端 mock coaching APIs...");

    try {
      const backendScenarios = await fetchScenarios();
      setScenarios(backendScenarios);
      setSelected((current) => backendScenarios.find((scenario) => scenario.id === current.id) ?? backendScenarios[0]);
      setSource("backend");
      setScenarioStatus("idle");
      setStatusText("已连接后端 mock coaching APIs。");
    } catch {
      setScenarios(localScenarios);
      setSelected((current) => localScenarios.find((scenario) => scenario.id === current.id) ?? localScenarios[0]);
      setSource("fallback");
      setScenarioStatus("error");
      setStatusText("后端暂不可用，已切换到前端本地 mock fallback。");
    }
  };

  const start = (scenario: Scenario) => {
    setSelected(scenario);
    setMessages([{ id: 1, sender: "ai", text: scenario.openingLine }]);
    setFeedback([]);
    setSummary(createLocalSummary([], []));
    setSendStatus("idle");
    setSummaryStatus("idle");
    setInput("");
    setView("practice");
  };

  const sendText = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text || sendStatus === "loading") return;

      const id = Date.now();
      const userMessage: Message = { id, sender: "user", text };
      const nextMessages = [...messages, userMessage];

      setMessages(nextMessages);
      setInput("");
      setSendStatus("loading");

      try {
        const [reply, turnFeedback] = await Promise.all([sendChatMessage(selected, nextMessages), fetchTurnFeedback(selected, userMessage)]);
        setMessages([...nextMessages, reply]);
        setFeedback((current) => [...current, turnFeedback]);
        setSource("backend");
        setSendStatus("idle");
        setStatusText("本轮 AI 回复和即时反馈来自后端 mock API。");
      } catch {
        setMessages([...nextMessages, createLocalReply(selected, nextMessages)]);
        setFeedback((current) => [...current, createLocalFeedback(text, id)]);
        setSource("fallback");
        setSendStatus("error");
        setStatusText("后端请求失败，本轮已使用前端本地 mock fallback。");
      }
    },
    [messages, selected, sendStatus],
  );

  const send = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendText(input);
  };

  const submitVoiceText = (text: string) => {
    if (!text || sendStatus === "loading") return;
    void sendText(text);
  };

  const endPractice = async () => {
    const fallbackSummary = createLocalSummary(messages, feedback);
    setSummary(fallbackSummary);
    setSummaryStatus("loading");
    setView("summary");

    try {
      const backendSummary = await fetchSessionSummary(selected, messages);
      setSummary(backendSummary);
      setSource("backend");
      setSummaryStatus("idle");
      setStatusText("课后总结和评分来自后端 mock API。");
    } catch {
      setSummary(fallbackSummary);
      setSource("fallback");
      setSummaryStatus("error");
      setStatusText("后端总结请求失败，已展示前端本地 mock fallback。");
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
      </header>

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
          feedback={feedback}
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
          onAgain={() => start(selected)}
          onChoose={() => setView("scenarios")}
        />
      )}
    </main>
  );
}

function Home({ onStart, source, statusText }: { onStart: () => void; source: SourceState; statusText: string }) {
  return (
    <section className="landing-grid page-section">
      <div className="hero-copy">
        <span className="eyebrow">{source === "backend" ? "Backend mock 已连接" : "Fallback mock 可稳定录屏"}</span>
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
  feedback,
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
  feedback: Feedback[];
  input: string;
  source: SourceState;
  statusText: string;
  sendStatus: AsyncState;
  onInput: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
  onSendText: (value: string) => void;
  onEnd: () => void;
  onReset: () => void;
}) {
  const turns = messages.filter((message) => message.sender === "user").length;
  const latestScore = feedback[feedback.length - 1]?.score ?? 82;
  const [speechLanguage, setSpeechLanguage] = useState("zh-CN");
  const latestAiMessage = [...messages].reverse().find((message) => message.sender === "ai");
  const latestAiText = latestAiMessage?.text ?? scenario.openingLine;
  const lastSpokenAiId = useRef<number | null>(null);
  const latestTranscriptRef = useRef("");
  const speechOutput = useSpeechOutput({ lang: "en-US", rate: 0.95, pitch: 1 });
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
      if (transcript) {
        onSendText(transcript);
        speechInput.resetTranscript();
        latestTranscriptRef.current = "";
      }
      return;
    }

    latestTranscriptRef.current = "";
    speechInput.resetTranscript();
    speechInput.startListening();
  };

  return (
    <section className="practice-shell page-section">
      <aside className="practice-context">
        <span className="difficulty">{scenario.level}</span>
        <h2>{scenario.title}</h2>
        <p>{scenario.description}</p>
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
        <TagList items={scenario.focus} />
        <button className="secondary-button" type="button" onClick={onReset}>
          更换场景
        </button>
      </aside>

      <div className="conversation-panel">
        <div className="panel-title">
          <div>
            <h2>对话练习</h2>
            <p>输入一句英文，查看后端 mock 的 AI 回复和即时反馈；后端不可用时自动 fallback。</p>
          </div>
          <button className="danger-button" type="button" onClick={onEnd} disabled={sendStatus === "loading"}>
            {sendStatus === "loading" ? "请稍等" : "结束练习"}
          </button>
        </div>
        <StatusBanner status={sendStatus} source={source} text={statusText} />
        <div className="practice-progress">
          <span>当前场景：{scenario.englishTitle}</span>
          <div aria-hidden="true">
            <span style={{ width: `${Math.min(100, messages.length * 14)}%` }} />
          </div>
          <strong>{turns} 轮</strong>
        </div>
        <div className="message-list" aria-live="polite">
          {messages.map((message) => (
            <article className={`message-bubble ${message.sender}`} key={message.id}>
              <div className="message-meta">
                <span>{message.sender === "ai" ? scenario.aiRole : "你"}</span>
                <button
                  className="read-aloud-button"
                  type="button"
                  onClick={() => speechOutput.speak(message.text)}
                  disabled={!speechOutput.isSupported || speechOutput.isSpeaking}
                >
                  {message.sender === "ai" ? "重播" : "朗读"}
                </button>
              </div>
              <p>{message.text}</p>
            </article>
          ))}
        </div>
        <VoiceControls
          input={speechInput}
          output={speechOutput}
          sampleText={latestAiText}
          language={speechLanguage}
          onLanguageChange={setSpeechLanguage}
          onToggleListening={toggleVoiceInput}
          isSending={sendStatus === "loading"}
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
          <p>改句、问题、升级表达、单轮分数。</p>
        </div>
        {feedback.length === 0 ? (
          <div className="empty-state">
            <strong>还没有反馈</strong>
            <p>发送一句英文后，这里会出现 corrected sentence、issue、better expression 和 score。</p>
          </div>
        ) : (
          <div className="feedback-list">
            {feedback.map((item) => (
              <article className="feedback-card" key={item.id}>
                <div className="score-pill">{item.score}</div>
                <div>
                  <span>Corrected sentence</span>
                  <p>{item.corrected}</p>
                </div>
                <div>
                  <span>Issue</span>
                  <p>{item.issue}</p>
                </div>
                <div>
                  <span>Better expression</span>
                  <p>{item.better}</p>
                </div>
              </article>
            ))}
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
  onAgain,
  onChoose,
}: {
  scenario: Scenario;
  summary: SessionSummary;
  status: AsyncState;
  source: SourceState;
  statusText: string;
  onAgain: () => void;
  onChoose: () => void;
}) {
  return (
    <section className="summary-layout page-section">
      <div className="summary-hero">
        <span>{scenario.title} · 课后总结</span>
        <h1>{summary.scores.综合}</h1>
        <p>Overall feedback：{status === "loading" ? "正在向后端生成课后总结和评分..." : summary.overallPerformance}</p>
        <StatusBanner status={status} source={source} text={statusText} />
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
      <span>{status === "loading" ? "连接中" : source === "backend" ? "后端 mock" : "本地 fallback"}</span>
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
