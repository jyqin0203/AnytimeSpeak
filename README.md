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
- Storage: SQLite for username/password users and practice history; backend in-memory sessions for the active coaching flow
- AI integration: environment-variable based LLM configuration with mock mode fallback

## Current Status

The project includes a mock-first MVP practice loop: scenario selection with static story seeds, session-based role-play chat, latest-turn feedback with a `grammar`/`naturalness`/`relevance`/`clarity` score breakdown, post-session summary, scoring, browser speech input/playback, user recording replay, and text input. The UI is Chinese-first for instructions and feedback labels while keeping practice content, AI role-play replies, and recommended English expressions in English.

The backend keeps demo sessions in memory, calls a real LLM when `LLM_PROVIDER_MODE=llm` and credentials are configured, and otherwise falls back to deterministic mock coaching. Every chat/feedback/summary response carries a `provider` field (`"llm"` or `"mock"`) so the frontend can show which one produced it without ever exposing the API key.

Username/password auth and practice history are supported. Users can register or log in from the topbar, then open `练习历史` to review saved sessions. Passwords are stored with salted PBKDF2 hashes, never as plaintext. The backend stores users, session metadata, messages, per-turn feedback, and post-session summaries in a local SQLite database (`backend/data/anytimespeak.db`). After each practice session the frontend automatically saves the record; users can log out, log back in, and still see their history. If saving fails, the completed session remains in the current frontend state as a pending save and the summary page shows a fallback note.

The practice page uses a fixed viewport-height layout so the message list, chat input, mic button, and end button are all visible without scrolling. The voice input is a compact single-row composer: a text field on the left, a small microphone button on the right (click once to start, click again to stop and send), and a send button. There is no separate language toggle. The post-session summary shows `—` while scores are loading instead of a placeholder number. AI reply text is sanitized to remove em dashes before display. Scenario difficulty and focus tags are displayed in Chinese; scenarios are sorted by level with beginner scenarios first.

## Local Development

### One-command development startup

Install dependencies first:

```bash
cd frontend
npm install
cd ../backend
pip install -r requirements.txt
```

Then start both services from the project root with one command:

```bash
npm run dev
```

Stop both services from the project root with:

```bash
npm run stop
```

On Windows, this runs `scripts/dev.bat` and opens separate terminal windows for the backend and frontend.
The stop command runs `scripts/stop-dev.bat` and stops processes listening on ports `5173` and `8000`.
On macOS/Linux, you can alternatively run:

```bash
sh scripts/dev.sh
sh scripts/stop-dev.sh
```

Development URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:8000`

The frontend runs Vite in development mode, so React/page changes are applied by HMR or browser refresh.
The backend runs `uvicorn app.main:app --reload`, so Python code changes under `backend/` reload the service automatically.
Changes to `.env` files, installed dependencies, Python package versions, Node package versions, or port configuration still require manually stopping and restarting the development servers.

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

### Doubao BigModel Streaming ASR

Doubao ASR is optional. The default `ASR_PROVIDER_MODE=browser` keeps the reproducible browser `SpeechRecognition` fallback. To enable the Volcano Engine BigModel ASR relay:

1. Open the Volcano Engine speech console and enable the BigModel speech recognition service.
2. Copy `.env.example` to `.env`.
3. Set the provider mode and credentials:

```env
ASR_PROVIDER_MODE=doubao
DOUBAO_API_KEY=your-new-console-app-key
DOUBAO_RESOURCE_ID=volc.seedasr.sauc.duration
DOUBAO_ASR_URL=wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async
DOUBAO_RESULT_TYPE=full
```

New console credentials use `DOUBAO_API_KEY` plus `DOUBAO_RESOURCE_ID`. Legacy console credentials can use `DOUBAO_APP_ID`, `DOUBAO_ASR_TOKEN`, and `DOUBAO_RESOURCE_ID` instead. Resource IDs are service-specific; common examples are `volc.bigasr.sauc.duration` for Doubao 1.0 and `volc.seedasr.sauc.duration` for Doubao 2.0.

`DOUBAO_ASR_URL` defaults to the recommended async bidirectional streaming endpoint, `wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async`. It can be changed to `.../bigmodel` for packet-by-packet bidirectional streaming or `.../bigmodel_nostream` for streaming-input mode. `DOUBAO_RESULT_TYPE` is optional and defaults to `full`; set it to `single` only when you want incremental transcript chunks.

When enabled, the frontend records microphone audio as PCM 16-bit, 16 kHz, mono and streams it to the backend `/ws/asr` relay. The backend connects to Doubao over WebSocket, sends the required binary ASR frames, and relays `partial` / `final` transcript events back to the browser. Missing or invalid Doubao configuration falls back to browser speech recognition or text input.

## Demo Video

Demo video link: TBD

Related preparation docs:

- Demo script: `docs/demo-script.md`
- MVP checklist: `docs/mvp-checklist.md`
- API contract: `docs/api-contract.md`
- Submission guide: `docs/submission-guide.md`

## Future Extension: End-to-End Voice AI Model

The current version supports Doubao (ByteDance) Streaming ASR for real-time Chinese-English mixed speech recognition as an optional backend provider. The architecture is designed so that a full end-to-end voice AI pipeline can be added without restructuring existing code:

- **Voice input (ASR)**: Real-time speech recognition via Doubao BigModel Streaming ASR WebSocket API, capturing PCM audio in the browser and streaming transcripts back through the backend relay (`/ws/asr`). Currently implemented as an optional provider (set `ASR_PROVIDER_MODE=doubao`).
- **Voice output (TTS)**: Cloud TTS services (e.g., Doubao TTS, Azure Cognitive Services TTS) can replace or supplement the current browser `SpeechSynthesis` by implementing the existing `SpeechOutputProvider` interface.
- **Pronunciation assessment**: A `PronunciationAssessmentProvider` interface is already defined in `frontend/src/speech/types.ts`. Cloud pronunciation scoring (e.g., Azure Pronunciation Assessment) can be plugged in without changing the practice flow.
- **Full end-to-end pipeline**: Combining Doubao ASR → LLM coaching → Doubao TTS would create a fully cloud-powered voice conversation loop. This is a planned direction but is **not implemented in the current version** to keep the MVP stable and reproducible without mandatory cloud credentials.

See `frontend/src/speech/types.ts` for the provider interfaces and `backend/app/asr_provider.py` for the Doubao ASR integration point.

## Originality and Third-Party Dependencies

- Original project code: project scaffold, backend health endpoint, frontend MVP flow, backend coaching endpoints, Doubao ASR provider integration, and documentation are maintained in this repository.
- Third-party libraries and frameworks: React, Vite, TypeScript, FastAPI, Uvicorn, Pytest, HTTPX, websockets, and volcengine-audio.
- AI APIs or AI-generated code usage: optional LLM provider calls and optional Doubao Streaming ASR are configured through environment variables; mock mode and browser fallback remain the defaults for reproducible demos. Environment variable placeholders are listed in `.env.example`.
- API keys, private credentials, and unauthorized assets must not be committed.

## Development Plan

Near-term PRs:

1. ~~Guest Profile and SQLite Practice History~~ — merged.
2. ~~Practice layout and UI/UX improvements~~ — merged.
3. ~~Username/password login and practice history~~ — merged.
4. ~~Doubao Streaming ASR provider~~ — merged.
5. Final submission materials.

See `docs/pr-plan.md` for the detailed PR roadmap.
