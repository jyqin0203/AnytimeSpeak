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

The project is in the planning and documentation initialization stage. No frontend or backend business code has been implemented yet.

## Local Development

Setup commands will be added after the frontend and backend projects are initialized.

```bash
# Placeholder
# Frontend and backend startup commands will be documented in later PRs.
```

## Demo Video

Demo video link: TBD

## Originality and Third-Party Dependencies

- Original project code: TBD as implementation begins.
- Third-party libraries and frameworks: TBD as dependencies are added.
- AI APIs or AI-generated code usage: TBD and will be documented in each related PR.
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
