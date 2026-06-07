# AnytimeSpeak

AnytimeSpeak is an AI English speaking practice project for scenario-based conversation training. The MVP helps users choose a scenario, practice an English conversation, receive grammar and expression feedback, end the session, and review a scored summary.

## Core Feature Plan

- Scenario selection: interview, restaurant ordering, and meeting.
- Session-based practice flow with static story seeds.
- AI role-play replies based on the selected scenario.
- Grammar correction and expression improvement suggestions.
- Latest-turn feedback with score breakdown.
- Post-session summary.
- Quantitative scoring for grammar, expression, fluency, scenario completion, and overall performance.
- Browser speech input, AI speech playback, user recording replay, and text fallback.

## Planned Tech Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- Speech input: browser `SpeechRecognition`
- Speech playback: browser `SpeechSynthesis`
- MVP storage: frontend state and backend in-memory sessions; SQLite is planned for lightweight guest profiles and practice history
- AI integration: environment-variable based LLM configuration with mock mode fallback

## Current Status

The project includes a mock-first MVP practice loop: scenario selection with static story seeds, session-based role-play chat, latest-turn feedback with a `grammar`/`naturalness`/`relevance`/`clarity` score breakdown, post-session summary, scoring, browser speech input/playback, user recording replay, and text input fallback. The UI is Chinese-first for instructions and feedback labels while keeping practice content, AI role-play replies, and recommended English expressions in English.

The backend keeps demo sessions in memory, calls a real LLM when `LLM_PROVIDER_MODE=llm` and credentials are configured, and otherwise falls back to deterministic mock coaching. Every chat/feedback/summary response carries a `provider` field (`"llm"` or `"mock"`) so the frontend can show which one produced it without ever exposing the API key.

Guest Profile and SQLite Practice History are planned / in progress outside current `main`. They should be treated as optional demo enhancements until their API, UI, and README status are merged and verified. Full username/password login and cloud-synced history remain future work.

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will print the local frontend URL in the terminal, usually `http://localhost:5173`.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

### Environment Variables

Copy `.env.example` to `.env` for local provider configuration. Do not commit `.env` or real API keys.
The backend automatically loads provider variables from `.env` in the project root or `backend/.env`, while shell environment variables still take priority.
Real provider mode requires `LLM_PROVIDER_MODE=llm`, an `LLM_API_KEY` or `OPENAI_API_KEY`, plus explicit `LLM_BASE_URL` and `LLM_MODEL` values. Missing configuration falls back to mock mode with a safe reason code.

## Demo Video

Demo video link: TBD

Related preparation docs:

- Demo script: `docs/demo-script.md`
- MVP checklist: `docs/mvp-checklist.md`
- API contract: `docs/api-contract.md`
- Submission guide: `docs/submission-guide.md`

## Originality and Third-Party Dependencies

- Original project code: project scaffold, backend health endpoint, frontend MVP flow, backend coaching endpoints, and documentation are maintained in this repository.
- Third-party libraries and frameworks: React, Vite, TypeScript, FastAPI, Uvicorn, Pytest, and HTTPX.
- AI APIs or AI-generated code usage: optional LLM provider calls are configured through environment variables; mock mode remains the default for reproducible demos. LLM environment variable placeholders are listed in `.env.example`.
- API keys, private credentials, and unauthorized assets must not be committed.

## Development Plan

Near-term PRs:

1. Guest Profile and SQLite Practice History, if not already merged.
2. Practice layout and demo usability improvements.
3. Username/password login and more stable practice history.
4. Streaming ASR provider.
5. Final submission materials.

See `docs/pr-plan.md` for the detailed PR roadmap.
