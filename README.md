# AnytimeSpeak

AnytimeSpeak is an AI English speaking practice project for scenario-based conversation training. The MVP will help users choose a scenario, practice an English conversation, receive grammar and expression feedback, end the session, and review a scored summary.

## Core Feature Plan

- Scenario selection: interview, restaurant ordering, and meeting.
- Text-based practice flow as the first stable MVP path.
- AI role-play replies based on the selected scenario.
- Grammar correction and expression improvement suggestions.
- Post-session summary.
- Quantitative scoring for grammar, expression, fluency, scenario completion, and overall performance.
- Browser speech input and speech playback as progressive enhancements.

## Planned Tech Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- Speech input: browser `SpeechRecognition`
- Speech playback: browser `SpeechSynthesis`
- MVP storage: `localStorage` or mock data
- AI integration: environment-variable based LLM configuration with mock mode fallback

## Current Status

The project has a minimal frontend and backend scaffold. No scenario selection, AI conversation, speech feature, database, or other business flow has been implemented yet.

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

Copy `.env.example` to `.env` for local provider configuration when LLM integration is added later. Do not commit `.env` or real API keys.

## Demo Video

Demo video link: TBD

## Originality and Third-Party Dependencies

- Original project code: project scaffold, backend health endpoint, and documentation are maintained in this repository.
- Third-party libraries and frameworks: React, Vite, TypeScript, FastAPI, Uvicorn, Pytest, and HTTPX.
- AI APIs or AI-generated code usage: no AI API is integrated yet. LLM environment variable placeholders are listed in `.env.example`.
- API keys, private credentials, and unauthorized assets must not be committed.

## Development Plan

Near-term PRs:

1. Project guidelines and planning documents.
2. Project initialization.
3. Frontend foundation.
4. Scenario selection.
5. Practice page with text input and mock AI replies.
6. Backend basic API.
7. Frontend and backend integration.
8. Speech input and playback.
9. Feedback, post-session summary, and scoring.

See `docs/pr-plan.md` for the detailed PR roadmap.
