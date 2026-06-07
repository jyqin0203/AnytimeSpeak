# API Contract

This document records the current AnytimeSpeak API shape. The current `main` branch implements the session-based coaching endpoints: `/api/health`, `/api/scenarios`, `/api/sessions`, `/api/chat`, `/api/feedback`, and `/api/summary`.

Guest Profile and Practice History endpoints are planned in PR13 / active iteration, but they are not part of the current `main` API unless that PR has been merged.

## General Rules

- Base path: `/api`
- Request and response bodies use JSON.
- Coaching endpoints use snake_case JSON fields.
- Session-based coaching requests carry `scenario_id`, `latest_user_message`, and `conversation_history` so the backend can inject the scenario story, roles, goal, and previous turns into prompts.
- `/api/feedback` evaluates only `latest_user_message`; `conversation_history` is context only.
- Mock responses should be deterministic enough for demo recording.
- API keys, provider tokens, and `.env` contents must never be returned to the frontend.
- Error responses should use a predictable shape.

```json
{
  "error": {
    "code": "invalid_request",
    "message": "scenario_id is required."
  }
}
```

## Provider And Fallback Semantics

`provider` is an informational string returned by `/api/chat`, `/api/feedback`, `/api/summary`, and chat `quick_feedback`.

- `"llm"` means the backend successfully generated the result through the configured LLM provider.
- `"mock"` means the backend returned deterministic mock coaching, either because `LLM_PROVIDER_MODE` is not `llm`, required provider env vars are missing, or the live provider call failed.
- `fallback_reason` may explain why the backend used mock mode. It must not include secrets, raw API keys, full request payloads, or raw provider error text.

This is different from the frontend local fallback. Backend mock fallback still means the frontend reached the backend and received a valid API response. Frontend local fallback means the browser could not use the backend response for that call, for example because the backend was unavailable, timed out, returned an error, or returned invalid JSON. Frontend local fallback is a UI resilience behavior, not a backend API provider value.

## Current Implemented Coaching Contract

### GET /api/health

Checks whether the backend service is running.

Current status: implemented.

Response example:

```json
{
  "status": "ok"
}
```

### GET /api/scenarios

Returns the scenario list shown by the frontend. The current backend returns a JSON array, not an object wrapper. The stable scenarios include Interview, Restaurant Ordering, and Meeting; additional scenarios may also be present after those core paths.

Current status: implemented.

Response example:

```json
[
  {
    "id": "interview",
    "scenario_id": "interview",
    "title": "Interview",
    "title_zh": "面试",
    "level": "Intermediate",
    "ai_role": "Hiring manager",
    "user_role": "Job candidate",
    "goal": "Practice introducing yourself, explaining experience, and asking professional follow-up questions.",
    "story_seed_id": "interview_first_round",
    "story_intro_zh": "你正在参加一场初级岗位的视频面试...",
    "story_intro_en": "You are taking part in a video interview for an entry-level role...",
    "opening_line": "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?",
    "opening_message": "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?",
    "conversation_style": "Professional and supportive.",
    "feedback_focus": ["grammar", "naturalness", "scenario fit"],
    "useful_expressions": ["I contributed to...", "One challenge I faced was..."]
  }
]
```

### POST /api/sessions

Starts a practice session in backend memory. Each scenario ships with multiple static story seeds. When `story_seed_id` is omitted, the backend selects one of the scenario seeds; when provided, the backend uses that exact seed for deterministic demos and tests.

Current status: implemented.

Request example:

```json
{
  "scenario_id": "meeting",
  "story_seed_id": "meeting_standup"
}
```

Response example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "meeting",
  "scenario": {
    "id": "meeting",
    "scenario_id": "meeting",
    "title": "Meeting",
    "title_zh": "会议"
  },
  "story_seed_id": "meeting_standup",
  "story_intro_zh": "你正在参加一个简短的团队站会...",
  "story_intro_en": "You are joining a short team stand-up meeting...",
  "opening_message": "Let's start with your update. What progress have you made since our last meeting?",
  "messages": [],
  "created_at": "2026-06-07T03:50:00.000000+00:00"
}
```

### POST /api/chat

Sends the latest user message and receives the next role-play reply. The backend keeps the reply grounded in the selected scenario, story seed, and conversation history.

Current status: implemented.

Request example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "meeting",
  "latest_user_message": "I finished the first version, but I have some problem with API.",
  "conversation_history": [
    {
      "role": "assistant",
      "content": "Let's start with your update. What progress have you made since our last meeting?"
    }
  ]
}
```

Response example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "meeting",
  "reply": {
    "role": "assistant",
    "content": "Thanks for the update. What specific data fields do you need from the backend team?"
  },
  "quick_feedback": {
    "what_you_said": "I finished the first version, but I have some problem with API.",
    "recommended_english": "I finished the first version, but I have a problem with the API.",
    "score": 82,
    "score_breakdown": {
      "grammar": 80,
      "naturalness": 82,
      "relevance": 90,
      "clarity": 84
    },
    "provider": "mock",
    "fallback_reason": "provider_mode_not_llm"
  },
  "provider": "mock",
  "fallback_reason": "provider_mode_not_llm"
}
```

### POST /api/feedback

Generates latest-turn feedback. It grades only `latest_user_message`; earlier turns are context and are not re-scored.

Current status: implemented.

Request example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "interview",
  "latest_user_message": "I am graduated last year and I was responsible for make the report.",
  "conversation_history": []
}
```

Response example:

```json
{
  "what_you_said": "I am graduated last year and I was responsible for make the report.",
  "user_intent": "The learner is describing education and project responsibility.",
  "recommended_english": "I graduated last year and I was responsible for making the report.",
  "issue": "Use simple past for a completed graduation event and a gerund after responsible for.",
  "why": "These forms sound more natural and grammatically correct in an interview answer.",
  "more_natural_option": "I graduated last year and was responsible for preparing the report.",
  "score": 78,
  "score_breakdown": {
    "grammar": 74,
    "naturalness": 78,
    "relevance": 88,
    "clarity": 80
  },
  "provider": "mock",
  "fallback_reason": "provider_mode_not_llm"
}
```

### POST /api/summary

Returns a post-session summary and quantitative scores for the selected scenario.

Current status: implemented.

Request example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "meeting",
  "conversation_history": [
    {
      "role": "assistant",
      "content": "Let's start with your update. What progress have you made?"
    },
    {
      "role": "user",
      "content": "I finished the page, but I have some problem with API."
    }
  ]
}
```

Response example:

```json
{
  "scenario_id": "meeting",
  "summary": "You completed a short meeting update and described a blocker.",
  "strengths": ["You gave a relevant progress update."],
  "repeated_issues": ["Article and preposition use around API-related phrases."],
  "better_expressions": ["The main blocker is that I need the backend team to confirm the API response format."],
  "scenario_completion": "The learner shared progress and identified a blocker.",
  "next_practice_focus": "Practice giving updates with progress, blocker, and next step.",
  "scores": {
    "grammar": 78,
    "expression": 80,
    "fluency": 82,
    "scenario_completion": 84,
    "overall": 81
  },
  "provider": "mock",
  "fallback_reason": "provider_mode_not_llm"
}
```

## Guest Profile API

Guest Profile is a lightweight nickname-based profile design with no password or OAuth. It is planned for PR13 / active iteration and is not implemented on current `main` unless that PR has been merged.

Current status: planned / in progress outside current `main`.

### POST /api/users/guest

Creates a lightweight guest profile.

Planned request example:

```json
{
  "display_name": "Jiaying"
}
```

Planned response example:

```json
{
  "user_id": "user_66ee86e050be",
  "display_name": "Jiaying",
  "created_at": "2026-06-07T03:43:38.456180+00:00"
}
```

### GET /api/users/{user_id}

Returns the guest user's display name and creation timestamp. Returns HTTP 404 when the user does not exist.

Planned response example:

```json
{
  "user_id": "user_66ee86e050be",
  "display_name": "Jiaying",
  "created_at": "2026-06-07T03:43:38.456180+00:00"
}
```

Planned endpoint summary:

- `POST /api/users/guest`
- `GET /api/users/{user_id}`

## Practice History API

Practice History is planned to persist completed sessions, messages, per-turn feedback, and summaries in local SQLite. SQLite runtime database files are ignored by `.gitignore` and must not be committed.

Current status: planned / in progress outside current `main`.

### POST /api/history/sessions

Saves a completed practice session including messages, feedback, summary, scores, and provider. Returns HTTP 404 if `user_id` is not found.

Planned request example:

```json
{
  "user_id": "user_66ee86e050be",
  "session_id": "session_abc123",
  "scenario_id": "interview",
  "scenario_title": "Interview",
  "story_intro_zh": "You are in an interview practice context.",
  "story_intro_en": "You are joining an interview.",
  "messages": [
    { "role": "assistant", "content": "Could you introduce yourself?" },
    { "role": "user", "content": "I am a software engineer." }
  ],
  "feedbacks": [
    {
      "user_message": "I am a software engineer.",
      "feedback_json": { "issue": "Clear answer.", "score_breakdown": {} },
      "score": 85
    }
  ],
  "summary": {
    "summary": "Good session.",
    "strengths": ["Clear introduction."],
    "repeated_issues": [],
    "better_expressions": []
  },
  "scores": { "overall": 85 },
  "overall_score": 85,
  "provider": "mock"
}
```

Planned response example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "interview",
  "scenario_title": "Interview",
  "started_at": "2026-06-07T03:50:00.000000+00:00",
  "overall_score": 85,
  "summary_preview": "Good session.",
  "provider": "mock"
}
```

### GET /api/history/sessions?user_id={user_id}

Returns the user's practice sessions in reverse chronological order.

Planned response example:

```json
[
  {
    "session_id": "session_abc123",
    "scenario_id": "interview",
    "scenario_title": "Interview",
    "started_at": "2026-06-07T03:50:00.000000+00:00",
    "overall_score": 85,
    "summary_preview": "Good session.",
    "provider": "mock"
  }
]
```

### GET /api/history/sessions/{session_id}

Returns the full detail of a saved practice session: scenario info, messages, feedback records, summary JSON, scores, and provider. Returns HTTP 404 when the session does not exist.

Planned response example:

```json
{
  "session_id": "session_abc123",
  "scenario_id": "interview",
  "scenario_title": "Interview",
  "story_intro_zh": "You are in an interview practice context.",
  "story_intro_en": "You are joining an interview.",
  "started_at": "2026-06-07T03:50:00.000000+00:00",
  "ended_at": "2026-06-07T03:55:00.000000+00:00",
  "overall_score": 85,
  "summary_json": {
    "summary": "Good session.",
    "strengths": ["Clear introduction."],
    "repeated_issues": [],
    "better_expressions": []
  },
  "provider": "mock",
  "messages": [
    { "role": "assistant", "content": "Could you introduce yourself?" },
    { "role": "user", "content": "I am a software engineer." }
  ],
  "feedbacks": [
    {
      "user_message": "I am a software engineer.",
      "feedback_json": { "issue": "Clear answer." },
      "score": 85
    }
  ]
}
```

Planned endpoint summary:

- `POST /api/history/sessions`
- `GET /api/history/sessions?user_id={user_id}`
- `GET /api/history/sessions/{session_id}`

## Legacy Draft Examples

The older draft examples below used camelCase fields such as `sessionId`, `scenarioId`, `messages`, `quickFeedback`, and `isMock`. They are retained only as legacy draft references. New frontend/backend work should use the current implemented snake_case contract above.
