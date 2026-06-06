import { FormEvent, useMemo, useState } from "react";
import "./App.css";

type View = "home" | "scenarios" | "practice" | "summary";
type Sender = "ai" | "user";

type Scenario = {
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

type Message = { id: number; sender: Sender; text: string };
type Feedback = { id: number; corrected: string; issue: string; better: string; score: number };

const scenarios: Scenario[] = [
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
    id: "food",
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
  {
    id: "travel",
    title: "旅行求助",
    englishTitle: "Travel",
    description: "练习酒店入住、问路、确认预订和解决简单旅行问题。",
    aiRole: "酒店前台",
    userRole: "旅行者",
    goal: "清楚提出需求，确认细节，并礼貌处理旅行中的小问题。",
    level: "入门",
    duration: "6 分钟",
    focus: ["信息确认", "礼貌求助", "问题解决"],
    openingLine: "Good evening. Welcome to the hotel. How can I help you today?",
    replies: [
      "I can help with that. Could you tell me your reservation name and arrival date?",
      "Thank you. We have your booking. Would you prefer a quiet room or a higher floor?",
      "No problem. I will update that for you. Is there anything else you need?",
    ],
  },
  {
    id: "daily",
    title: "日常闲聊",
    englishTitle: "Daily Conversation",
    description: "练习自然开场、回应和延续话题，让英文对话不再卡住。",
    aiRole: "友好邻居",
    userRole: "英语学习者",
    goal: "开启轻松对话，回应自然，并用追问把交流延续下去。",
    level: "入门",
    duration: "5 分钟",
    focus: ["自然回应", "追问技巧", "轻松表达"],
    openingLine: "Hi there! I do not think we have met before. How is your day going?",
    replies: [
      "That sounds nice. What do you usually like to do after work or class?",
      "Interesting. I have been looking for new ideas. What would you recommend?",
      "Thanks for sharing. It was nice talking with you. Hope to see you again soon.",
    ],
  },
];

const features = ["场景化练习", "AI 角色对话", "语法 / 表达反馈", "课后总结评分"];
const marketNotes = ["先明确场景目标", "对话主线不被反馈打断", "结束后沉淀分项评分与复用表达"];
const expressions = [
  "I would like to learn more about...",
  "Could you clarify what you mean by...?",
  "My main contribution was...",
  "I would prefer..., if possible.",
];

function App() {
  const [view, setView] = useState<View>("home");
  const [selected, setSelected] = useState(scenarios[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [input, setInput] = useState("");

  const scores = useMemo(() => {
    const avg = feedback.length ? Math.round(feedback.reduce((sum, item) => sum + item.score, 0) / feedback.length) : 82;
    const turns = messages.filter((message) => message.sender === "user").length;
    return {
      语法: Math.min(96, avg + 2),
      表达: Math.min(94, avg + 4),
      流畅: turns > 1 ? 86 : 78,
      完成度: turns > 2 ? 90 : 82,
      综合: Math.round((avg + 86 + 84 + 88) / 4),
    };
  }, [feedback, messages]);

  const start = (scenario: Scenario) => {
    setSelected(scenario);
    setMessages([{ id: 1, sender: "ai", text: scenario.openingLine }]);
    setFeedback([]);
    setInput("");
    setView("practice");
  };

  const send = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = input.trim();
    if (!text) return;
    const turn = messages.filter((message) => message.sender === "user").length;
    const id = Date.now();
    setMessages((current) => [
      ...current,
      { id, sender: "user", text },
      { id: id + 1, sender: "ai", text: selected.replies[turn % selected.replies.length] },
    ]);
    setFeedback((current) => [...current, createFeedback(text, current.length)]);
    setInput("");
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

      {view === "home" && <Home onStart={() => setView("scenarios")} />}
      {view === "scenarios" && <Scenarios selected={selected} onSelect={setSelected} onStart={start} />}
      {view === "practice" && (
        <Practice
          scenario={selected}
          messages={messages}
          feedback={feedback}
          input={input}
          onInput={setInput}
          onSend={send}
          onEnd={() => setView("summary")}
          onReset={() => setView("scenarios")}
        />
      )}
      {view === "summary" && (
        <Summary scenario={selected} scores={scores} feedback={feedback} onAgain={() => start(selected)} onChoose={() => setView("scenarios")} />
      )}
    </main>
  );
}

function Home({ onStart }: { onStart: () => void }) {
  return (
    <section className="landing-grid page-section">
      <div className="hero-copy">
        <span className="eyebrow">Mock 模式 · 可稳定录屏</span>
        <h1>随时开口练英语</h1>
        <p className="product-positioning">AnytimeSpeak · AI English Speaking Coach</p>
        <p className="hero-description">从真实场景进入对话，边练边看语法和表达建议，结束后获得一份清晰的口语能力总结。</p>
        <div className="hero-actions">
          <button className="primary-button" type="button" onClick={onStart}>
            开始练习
          </button>
          <span>无需后端、无需 API Key</span>
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
  onSelect,
  onStart,
}: {
  selected: Scenario;
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
  onInput,
  onSend,
  onEnd,
  onReset,
}: {
  scenario: Scenario;
  messages: Message[];
  feedback: Feedback[];
  input: string;
  onInput: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
  onEnd: () => void;
  onReset: () => void;
}) {
  const turns = messages.filter((message) => message.sender === "user").length;
  const latestScore = feedback[feedback.length - 1]?.score ?? 82;

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
            <p>输入一句英文，查看本地 mock 的 AI 回复和即时反馈。</p>
          </div>
          <button className="danger-button" type="button" onClick={onEnd}>
            结束练习
          </button>
        </div>
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
              <span>{message.sender === "ai" ? scenario.aiRole : "你"}</span>
              <p>{message.text}</p>
            </article>
          ))}
        </div>
        <form className="composer" onSubmit={onSend}>
          <label htmlFor="practice-input">你的英文回答</label>
          <div>
            <input
              id="practice-input"
              value={input}
              onChange={(event) => onInput(event.target.value)}
              placeholder="例如：I finished the homepage and need help with tests."
            />
            <button className="primary-button" type="submit">
              发送
            </button>
          </div>
        </form>
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
  scores,
  feedback,
  onAgain,
  onChoose,
}: {
  scenario: Scenario;
  scores: Record<string, number>;
  feedback: Feedback[];
  onAgain: () => void;
  onChoose: () => void;
}) {
  const mistakes = feedback.length ? feedback.map((item) => item.issue) : ["建议至少完成 2-3 轮对话，让总结更有参考价值。"];

  return (
    <section className="summary-layout page-section">
      <div className="summary-hero">
        <span>{scenario.title} · 课后总结</span>
        <h1>{scores.综合}</h1>
        <p>Overall feedback：你已经完成本次场景练习，回答方向清楚。下一步可以尝试增加细节、连接词和更自然的礼貌表达。</p>
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

      <div className="summary-columns">
        <SummaryList title="优势" items={["能围绕场景目标给出直接回答。", "对话没有偏离角色设定，适合继续扩展。", "已经使用了可理解的基础职场 / 日常词汇。"]} />
        <SummaryList title="常见问题" items={mistakes.slice(0, 3)} />
        <SummaryList title="建议复用表达" items={expressions} />
      </div>
    </section>
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

function createFeedback(input: string, index: number): Feedback {
  const text = input.trim();
  const sentence = text.endsWith(".") || text.endsWith("?") || text.endsWith("!") ? text : `${text}.`;
  const corrected = sentence.charAt(0).toUpperCase() + sentence.slice(1);
  return {
    id: Date.now() + index,
    corrected,
    issue: index % 2 === 0 ? "句子意思清楚，但开头需要大写，并尽量补完整句号。" : "表达可理解，但可以更自然、更像真实对话。",
    better: index % 2 === 0 ? "I would like to add one specific example to explain my answer." : "Could you give me a little more detail about the next step?",
    score: Math.min(94, 78 + index * 4 + Math.min(8, Math.floor(text.length / 18))),
  };
}

export default App;
