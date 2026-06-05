import { FormEvent, useMemo, useState } from "react";
import "./App.css";

type View = "landing" | "scenarios" | "practice" | "summary";
type Sender = "ai" | "user";

type Scenario = {
  id: string;
  title: string;
  description: string;
  aiRole: string;
  userRole: string;
  goal: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  openingLine: string;
  replies: string[];
};

type Message = {
  id: number;
  sender: Sender;
  text: string;
};

type Feedback = {
  id: number;
  original: string;
  correctedSentence: string;
  issue: string;
  betterExpression: string;
  score: number;
};

const scenarios: Scenario[] = [
  {
    id: "interview",
    title: "Interview",
    description: "Practice answering hiring questions with a calm, professional tone.",
    aiRole: "Hiring manager",
    userRole: "Job candidate",
    goal: "Introduce yourself, explain your experience, and ask a smart follow-up question.",
    difficulty: "Intermediate",
    openingLine:
      "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?",
    replies: [
      "Thanks for sharing that. Can you describe one project where you made a clear impact?",
      "That sounds useful. What challenge did you face, and how did you handle it?",
      "Good example. Before we finish, what would you like to know about the team or role?",
    ],
  },
  {
    id: "ordering-food",
    title: "Ordering Food",
    description: "Rehearse a restaurant conversation from recommendations to final order.",
    aiRole: "Restaurant server",
    userRole: "Customer",
    goal: "Order food, ask about recommendations, and clarify preferences politely.",
    difficulty: "Beginner",
    openingLine: "Welcome! Are you ready to order, or would you like a few recommendations first?",
    replies: [
      "Of course. Our grilled salmon is popular today. Do you have any allergies or preferences?",
      "Great choice. Would you like that with rice, salad, or roasted vegetables?",
      "Perfect. I will place that order for you. Would you like anything to drink?",
    ],
  },
  {
    id: "meeting",
    title: "Meeting",
    description: "Build confidence sharing progress, blockers, and next steps at work.",
    aiRole: "Team lead",
    userRole: "Team member",
    goal: "Give a progress update, discuss blockers, and agree on next steps.",
    difficulty: "Intermediate",
    openingLine: "Let's start with your update. What progress have you made since our last meeting?",
    replies: [
      "Thanks for the update. Is anything blocking the remaining work right now?",
      "That is clear. What support do you need from the team this week?",
      "Good. Please confirm the next step and when you expect to finish it.",
    ],
  },
  {
    id: "travel",
    title: "Travel",
    description: "Practice asking for help with directions, booking, and simple travel issues.",
    aiRole: "Hotel receptionist",
    userRole: "Traveler",
    goal: "Ask clear questions, confirm details, and solve a travel problem.",
    difficulty: "Beginner",
    openingLine: "Good evening. Welcome to the hotel. How can I help you today?",
    replies: [
      "I can help with that. Could you tell me your reservation name and arrival date?",
      "Thank you. We have your booking. Would you prefer a quiet room or a higher floor?",
      "No problem. I will update that for you. Is there anything else you need?",
    ],
  },
  {
    id: "daily-conversation",
    title: "Daily Conversation",
    description: "Practice natural small talk for everyday social situations.",
    aiRole: "Friendly neighbor",
    userRole: "English learner",
    goal: "Start a casual conversation, respond naturally, and keep the exchange going.",
    difficulty: "Beginner",
    openingLine: "Hi there! I do not think we have met before. How is your day going?",
    replies: [
      "That sounds nice. What do you usually like to do after work or class?",
      "Interesting. I have been looking for new ideas. What would you recommend?",
      "Thanks for sharing. It was nice talking with you. Hope to see you again soon.",
    ],
  },
];

const featureHighlights = [
  "Scenario-based practice",
  "AI role-play conversation",
  "Grammar and expression feedback",
  "Post-session summary",
];

const suggestedExpressions = [
  "I would like to learn more about...",
  "Could you clarify what you mean by...?",
  "My main contribution was...",
  "I would prefer..., if possible.",
];

function App() {
  const [view, setView] = useState<View>("landing");
  const [selectedScenario, setSelectedScenario] = useState<Scenario>(scenarios[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [inputValue, setInputValue] = useState("");

  const summaryScores = useMemo(() => {
    const averageFeedback =
      feedback.length > 0
        ? Math.round(feedback.reduce((total, item) => total + item.score, 0) / feedback.length)
        : 82;

    return {
      grammar: Math.min(96, averageFeedback + 2),
      expression: Math.min(94, averageFeedback + 4),
      fluency: messages.filter((message) => message.sender === "user").length > 1 ? 86 : 78,
      completion: messages.filter((message) => message.sender === "user").length > 2 ? 90 : 82,
      overall: Math.round((averageFeedback + 86 + 84 + 88) / 4),
    };
  }, [feedback, messages]);

  const startScenario = (scenario: Scenario) => {
    setSelectedScenario(scenario);
    setMessages([{ id: 1, sender: "ai", text: scenario.openingLine }]);
    setFeedback([]);
    setInputValue("");
    setView("practice");
  };

  const sendMessage = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedInput = inputValue.trim();

    if (!trimmedInput) {
      return;
    }

    const userTurnCount = messages.filter((message) => message.sender === "user").length;
    const nextId = messages.length + feedback.length + 2;
    const aiReply =
      selectedScenario.replies[userTurnCount % selectedScenario.replies.length] ??
      "Thanks. Please continue with one more detail so we can complete the practice goal.";

    setMessages((currentMessages) => [
      ...currentMessages,
      { id: nextId, sender: "user", text: trimmedInput },
      { id: nextId + 1, sender: "ai", text: aiReply },
    ]);

    setFeedback((currentFeedback) => [
      ...currentFeedback,
      createMockFeedback(trimmedInput, currentFeedback.length),
    ]);

    setInputValue("");
  };

  const resetPractice = () => {
    setMessages([]);
    setFeedback([]);
    setInputValue("");
    setView("scenarios");
  };

  return (
    <main className="app">
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => setView("landing")}>
          <span className="brand-mark">AS</span>
          <span>AnytimeSpeak</span>
        </button>
        <nav aria-label="Practice flow">
          <button type="button" onClick={() => setView("landing")} className={view === "landing" ? "active" : ""}>
            Home
          </button>
          <button type="button" onClick={() => setView("scenarios")} className={view === "scenarios" ? "active" : ""}>
            Scenarios
          </button>
          <button
            type="button"
            onClick={() => startScenario(selectedScenario)}
            className={view === "practice" ? "active" : ""}
          >
            Practice
          </button>
        </nav>
      </header>

      {view === "landing" && <LandingPage onStart={() => setView("scenarios")} />}
      {view === "scenarios" && (
        <ScenarioSelection selectedScenario={selectedScenario} onSelect={setSelectedScenario} onStart={startScenario} />
      )}
      {view === "practice" && (
        <PracticePage
          scenario={selectedScenario}
          messages={messages}
          feedback={feedback}
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSend={sendMessage}
          onEnd={() => setView("summary")}
          onReset={resetPractice}
        />
      )}
      {view === "summary" && (
        <SummaryPage
          scenario={selectedScenario}
          scores={summaryScores}
          feedback={feedback}
          onPracticeAgain={() => startScenario(selectedScenario)}
          onChooseScenario={() => setView("scenarios")}
        />
      )}
    </main>
  );
}

function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <section className="landing-grid page-section">
      <div className="hero-copy">
        <h1>AnytimeSpeak</h1>
        <p className="product-positioning">AI English Speaking Coach</p>
        <p className="hero-description">
          Practice realistic English conversations, get lightweight feedback after each turn, and finish with a clear
          score summary you can use for the next session.
        </p>
        <button className="primary-button" type="button" onClick={onStart}>
          Start Practice
        </button>
      </div>

      <div className="hero-panel" aria-label="Practice preview">
        <div className="hero-panel-header">
          <span>Live demo loop</span>
          <span className="status-dot">Mock mode</span>
        </div>
        <div className="preview-chat">
          <p className="preview-message ai">Could you briefly introduce yourself?</p>
          <p className="preview-message user">I am a frontend developer and I enjoy building useful products.</p>
          <div className="preview-feedback">
            <strong>Better expression</strong>
            <span>I have experience building user-focused web products.</span>
          </div>
        </div>
      </div>

      <div className="feature-strip" aria-label="Core features">
        {featureHighlights.map((feature) => (
          <article className="feature-item" key={feature}>
            <span />
            <p>{feature}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScenarioSelection({
  selectedScenario,
  onSelect,
  onStart,
}: {
  selectedScenario: Scenario;
  onSelect: (scenario: Scenario) => void;
  onStart: (scenario: Scenario) => void;
}) {
  return (
    <section className="page-section">
      <div className="section-heading">
        <h2>Choose a practice scenario</h2>
        <p>Select one realistic conversation and rehearse a complete English speaking path.</p>
      </div>

      <div className="scenario-grid">
        {scenarios.map((scenario) => (
          <button
            className={`scenario-card ${selectedScenario.id === scenario.id ? "selected" : ""}`}
            key={scenario.id}
            type="button"
            onClick={() => onSelect(scenario)}
          >
            <span className="difficulty">{scenario.difficulty}</span>
            <h3>{scenario.title}</h3>
            <p>{scenario.description}</p>
            <dl>
              <div>
                <dt>AI role</dt>
                <dd>{scenario.aiRole}</dd>
              </div>
              <div>
                <dt>Goal</dt>
                <dd>{scenario.goal}</dd>
              </div>
            </dl>
          </button>
        ))}
      </div>

      <div className="scenario-action">
        <div>
          <span>Selected scenario</span>
          <strong>{selectedScenario.title}</strong>
        </div>
        <button className="primary-button" type="button" onClick={() => onStart(selectedScenario)}>
          Start {selectedScenario.title}
        </button>
      </div>
    </section>
  );
}

function PracticePage({
  scenario,
  messages,
  feedback,
  inputValue,
  onInputChange,
  onSend,
  onEnd,
  onReset,
}: {
  scenario: Scenario;
  messages: Message[];
  feedback: Feedback[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: (event: FormEvent<HTMLFormElement>) => void;
  onEnd: () => void;
  onReset: () => void;
}) {
  return (
    <section className="practice-shell page-section">
      <aside className="practice-context">
        <span className="difficulty">{scenario.difficulty}</span>
        <h2>{scenario.title}</h2>
        <p>{scenario.description}</p>
        <dl>
          <div>
            <dt>AI role</dt>
            <dd>{scenario.aiRole}</dd>
          </div>
          <div>
            <dt>Your role</dt>
            <dd>{scenario.userRole}</dd>
          </div>
          <div>
            <dt>Practice goal</dt>
            <dd>{scenario.goal}</dd>
          </div>
        </dl>
        <button className="secondary-button" type="button" onClick={onReset}>
          Change Scenario
        </button>
      </aside>

      <div className="conversation-panel">
        <div className="panel-title">
          <div>
            <h2>Practice conversation</h2>
            <p>Type one English sentence to receive a mock AI reply and feedback.</p>
          </div>
          <button className="danger-button" type="button" onClick={onEnd}>
            End Session
          </button>
        </div>

        <div className="message-list" aria-live="polite">
          {messages.map((message) => (
            <article className={`message-bubble ${message.sender}`} key={message.id}>
              <span>{message.sender === "ai" ? scenario.aiRole : "You"}</span>
              <p>{message.text}</p>
            </article>
          ))}
        </div>

        <form className="composer" onSubmit={onSend}>
          <label htmlFor="practice-input">Your response</label>
          <div>
            <input
              id="practice-input"
              value={inputValue}
              onChange={(event) => onInputChange(event.target.value)}
              placeholder="Type your English response..."
            />
            <button className="primary-button" type="submit">
              Send
            </button>
          </div>
        </form>
      </div>

      <aside className="feedback-panel">
        <div className="panel-title compact">
          <h2>Turn feedback</h2>
          <p>Local mock corrections for demo recording.</p>
        </div>
        {feedback.length === 0 ? (
          <div className="empty-state">
            <strong>No feedback yet</strong>
            <p>Send a sentence to see correction, issue, better expression, and score.</p>
          </div>
        ) : (
          <div className="feedback-list">
            {feedback.map((item) => (
              <article className="feedback-card" key={item.id}>
                <div className="score-pill">{item.score}</div>
                <div>
                  <span>Corrected sentence</span>
                  <p>{item.correctedSentence}</p>
                </div>
                <div>
                  <span>Issue</span>
                  <p>{item.issue}</p>
                </div>
                <div>
                  <span>Better expression</span>
                  <p>{item.betterExpression}</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </aside>
    </section>
  );
}

function SummaryPage({
  scenario,
  scores,
  feedback,
  onPracticeAgain,
  onChooseScenario,
}: {
  scenario: Scenario;
  scores: Record<"grammar" | "expression" | "fluency" | "completion" | "overall", number>;
  feedback: Feedback[];
  onPracticeAgain: () => void;
  onChooseScenario: () => void;
}) {
  const mistakes =
    feedback.length > 0
      ? feedback.map((item) => item.issue)
      : ["Add more complete sentences before ending the session."];

  return (
    <section className="summary-layout page-section">
      <div className="summary-hero">
        <span>{scenario.title} summary</span>
        <h1>{scores.overall}</h1>
        <p>
          Overall feedback: You completed the practice path and responded clearly. Keep building longer answers with
          more natural transitions and specific details.
        </p>
        <div className="summary-actions">
          <button className="primary-button" type="button" onClick={onPracticeAgain}>
            Practice Again
          </button>
          <button className="secondary-button" type="button" onClick={onChooseScenario}>
            Choose Scenario
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
        <SummaryList
          title="Strengths"
          items={[
            "You answered in a direct and understandable way.",
            "You stayed on topic for the selected scenario.",
            "You used practical vocabulary for the conversation goal.",
          ]}
        />
        <SummaryList title="Mistakes" items={mistakes.slice(0, 3)} />
        <SummaryList title="Suggested expressions" items={suggestedExpressions} />
      </div>
    </section>
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

function createMockFeedback(input: string, index: number): Feedback {
  const trimmed = input.trim();
  const sentence = trimmed.endsWith(".") || trimmed.endsWith("?") || trimmed.endsWith("!")
    ? trimmed
    : `${trimmed}.`;
  const capitalized = sentence.charAt(0).toUpperCase() + sentence.slice(1);
  const score = Math.min(94, 78 + index * 4 + Math.min(8, Math.floor(trimmed.length / 18)));

  return {
    id: Date.now() + index,
    original: input,
    correctedSentence: capitalized,
    issue:
      index % 2 === 0
        ? "Make the sentence complete and use clear capitalization."
        : "The meaning is clear, but the expression can sound more natural.",
    betterExpression:
      index % 2 === 0
        ? "I would like to add one specific example to explain my answer."
        : "Could you give me a little more detail about the next step?",
    score,
  };
}

export default App;
