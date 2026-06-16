# API Contract

This document records the current AnytimeSpeak backend API on `main`. If older PR notes conflict with this file, use current code plus this contract as the source of truth.

## General Rules

- Base path: `/api`.
- Request and response bodies use JSON unless an endpoint explicitly accepts `multipart/form-data`.
- Active coaching sessions are kept in backend memory for the current demo loop.
- Practice history, users, messages, feedback, and summaries are persisted in local SQLite.
- API keys, provider tokens, `.env` contents, raw provider errors, and private credentials must never be returned to the frontend.
- `provider` fields are informational labels only. They identify whether a result came from a real provider or fallback without exposing secrets.

## Provider And Fallback Model

Backend mock fallback and frontend local fallback are different:

- Backend mock fallback means the backend returned a valid API response using deterministic local rules.
- Frontend local fallback means the browser could not use the backend result and kept the demo moving with local data or local summary generation.

Coaching endpoints return `provider="llm"` after a successful real LLM call and `provider="mock"` when deterministic fallback produced the response. `fallback_reason` may be present, but it must contain only a safe reason code.

Pronunciation assessment returns `provider` and `is_fallback`. `provider="heuristic_mock"` means local transcript-based fallback produced the result.

## Implemented Endpoints

### GET /api/health

Checks whether the backend is running.

Response:

```json
{"status":"ok"}
```

### GET /api/scenarios

Returns the scenario list shown by the frontend. Scenarios include IDs, Chinese and English titles, roles, goals, story seed fields, opening messages, conversation style, feedback focus, and useful expressions.

Current status: implemented with static scenario catalog.

### POST /api/sessions

Starts a practice session in backend memory.

Request:

```json
{
  "scenario_id": "meeting",
  "story_seed_id": "meeting_weekly_sync"
}
```

`story_seed_id` is optional. If omitted, the backend selects one of the scenario's static story seeds. The response echoes the selected seed so later turns stay grounded in the same story.

### POST /api/chat

Sends the latest user message and receives the next role-play reply. This endpoint is intentionally limited to real-time dialogue and does not synchronously return per-turn feedback, summary, or pronunciation assessment.

Request:

```json
{
  "session_id": "session_demo",
  "scenario_id": "meeting",
  "latest_user_message": "I finished the page, but I have some problem with API.",
  "conversation_history": [
    {
      "role": "assistant",
      "content": "Let's start with your update. What progress have you made since our last meeting?"
    }
  ]
}
```

Response shape:

```json
{
  "session_id": "session_demo",
  "scenario_id": "meeting",
  "reply": {
    "role": "assistant",
    "content": "Thanks for the update. What specific API fields do you need from the backend team?"
  },
  "provider": "mock",
  "fallback_reason": null
}
```

### POST /api/feedback

Generates feedback for the latest user message. Previous turns are context only and are not re-scored.

Request fields:

- `session_id`
- `scenario_id`
- `latest_user_message`
- `conversation_history`

Response includes:

- `what_you_said`
- `user_intent`
- `recommended_english`
- `issue`
- `why`
- `more_natural_option`
- `score`
- `score_breakdown.grammar`
- `score_breakdown.naturalness`
- `score_breakdown.relevance`
- `score_breakdown.clarity`
- `provider`
- optional safe `fallback_reason`
- optional compatibility fields such as `corrected_sentence`, `better_expression`, `user_intent_zh`, `code_switching_tip`

### POST /api/summary

Generates a post-session summary and scores.

Request:

```json
{
  "session_id": "session_demo",
  "scenario_id": "interview",
  "conversation_history": [
    {"role": "assistant", "content": "Could you introduce yourself?"},
    {"role": "user", "content": "I worked in a team project before."}
  ]
}
```

Response includes:

- `summary`
- `strengths`
- `repeated_issues`
- `better_expressions`
- `scenario_completion`
- `next_practice_focus`
- optional `code_switching_advice`
- `scores.grammar`
- `scores.expression`
- `scores.fluency`
- `scores.scenario_completion`
- `scores.overall`
- `provider`
- optional safe `fallback_reason`

## ASR API

Speech recognition is optional. Text input must remain available.

### GET /api/asr/mode

Returns active ASR mode:

```json
{"asr_mode":"browser"}
```

Returns `"doubao"` only when `ASR_PROVIDER_MODE=doubao` and required Doubao credentials are present. Otherwise returns `"browser"`.

### WebSocket /ws/asr

Relays browser microphone audio to Doubao BigModel Streaming ASR when enabled.

Frontend sends:

```json
{"type":"config","lang":"zh-CN"}
```

Then sends PCM 16-bit, 16 kHz, mono binary audio chunks. When recording stops:

```json
{"type":"end"}
```

Backend sends:

```json
{"type":"ready"}
{"type":"partial","transcript":"Hello, this is a speaking test."}
{"type":"final","transcript":"Hello, this is a speaking test."}
{"type":"error","code":"network","message":"Doubao speech recognition is temporarily unavailable; switched back to browser speech recognition."}
```

Doubao credentials are backend-only. New console credentials use `DOUBAO_API_KEY` plus `DOUBAO_RESOURCE_ID`; legacy credentials can use `DOUBAO_APP_ID`, `DOUBAO_ASR_TOKEN`, and `DOUBAO_RESOURCE_ID`.

## Pronunciation API

### POST /api/pronunciation/assess

Scores pronunciation for voice turns. It is separate from `/api/feedback`: feedback handles grammar/expression/scenario fit, while pronunciation assessment handles pronunciation, fluency, accuracy, completeness, rhythm, and spoken delivery tips.

Current status: implemented with local `heuristic_mock` fallback, generic API provider mode, and optional iFlytek/XFYUN ISE provider mode.

JSON request:

```json
{
  "session_id": "session_demo",
  "scenario_id": "daily_conversation",
  "user_message": "What do you do recently?",
  "transcript": "What do you do recently?",
  "reference_text": "What have you been up to recently?",
  "audio_duration_ms": 3200,
  "recognized_language": "mixed"
}
```

Multipart request fields:

- `audio`: optional recording file, converted by frontend to mono 16 kHz PCM when possible.
- `session_id`
- `scenario_id`
- `user_message`
- `transcript`
- `reference_text`
- `audio_duration_ms`
- `recognized_language`
- `provider_mode`

Response:

```json
{
  "provider": "heuristic_mock",
  "pronunciation_score": 78,
  "fluency_score": 74,
  "accuracy_score": 80,
  "completeness_score": 82,
  "rhythm_score": 75,
  "overall_score": 78,
  "feedback_zh": "这句话整体可以听懂，但表达略不自然。",
  "strengths": ["语音输入内容完整"],
  "improvement_tips": ["可以跟读推荐句一次"],
  "word_tips": ["recently", "been up to"],
  "is_fallback": true
}
```

Missing configuration, timeouts, HTTP failures, WebSocket failures, and invalid provider schemas fall back to `heuristic_mock`.

## User Auth API

### POST /api/users/register

Creates a username/password user. Passwords are stored as salted PBKDF2 hashes.

Request:

```json
{"username":"demo_user","password":"demo-password"}
```

Response:

```json
{
  "user_id": "user_66ee86e050be",
  "username": "demo_user",
  "created_at": "2026-06-07T03:43:38.456180+00:00"
}
```

Returns HTTP 409 when the username already exists.

### POST /api/users/login

Authenticates an existing user.

Returns HTTP 401 for invalid credentials.

### GET /api/users/{user_id}

Returns user ID, username, and creation time. Returns HTTP 404 when missing.

## Practice History API

### POST /api/history/sessions

Saves a completed practice session including scenario info, messages, feedbacks, summary JSON, scores, overall score, and provider label. Pronunciation assessment is saved inside per-turn feedback JSON when available.

### GET /api/history/sessions?user_id={user_id}

Returns the user's saved sessions in reverse chronological order.

### GET /api/history/sessions/{session_id}

Returns full saved session detail: scenario info, messages, feedback records, summary JSON, overall score, and provider.

## Not Implemented In Current Main

- Cloud TTS provider endpoint.
- Cloud-synced multi-device history.
- Phoneme-level pronunciation visualization.
- Teacher dashboard or learning path API.
