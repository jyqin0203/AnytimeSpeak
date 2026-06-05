# PR Plan

This project should be developed through small, focused PRs. Each PR should keep `main` runnable and include a clear description, implementation approach, test method, and dependency/API disclosure.

## PR 1: Project Guidelines and Planning Documents

- Add `AGENTS.md`.
- Add project, PR, and product planning documents.
- Add README placeholders.
- Add `.gitignore`.

## PR 2: Project Initialization

- Initialize frontend and backend folders.
- Add basic package metadata and development commands.
- Add minimal health checks or placeholder scripts.
- Keep the app runnable without business features.

## PR 3: Frontend Foundation

- Add React + Vite + TypeScript setup.
- Add base layout, routing, and shared UI structure.
- Add a simple development page shell.

## PR 4: Scenario Selection

- Add scenario list for interview, restaurant ordering, and meeting.
- Add scenario metadata and selection state.
- Navigate from scenario selection to the practice page.

## PR 5: Practice Page

- Add conversation layout.
- Add user text input and message history.
- Add end-practice action.
- Use mock AI replies only.

## PR 6: Backend Basic API

- Add FastAPI app structure.
- Add health endpoint.
- Add mock chat endpoint.
- Add environment configuration pattern.

## PR 7: Frontend and Backend Integration

- Connect frontend practice page to backend chat endpoint.
- Add loading and error states.
- Keep mock mode available.

## PR 8: Speech Input

- Add browser `SpeechRecognition` support where available.
- Keep text input as fallback.
- Add clear unsupported-browser behavior.

## PR 9: Speech Playback

- Add browser `SpeechSynthesis` playback for AI replies.
- Add play, stop, and auto-play options.
- Keep text display as fallback.

## PR 10: Grammar and Expression Feedback

- Add feedback generation after user turns or at controlled checkpoints.
- Show grammar corrections and expression suggestions without over-interrupting practice.
- Support mock feedback for demos without API keys.

## PR 11: Post-Session Summary

- Add end-session summary flow.
- Summarize strengths, issues, useful expressions, and next practice suggestions.
- Store session summary locally for MVP.

## PR 12: Scoring System

- Add grammar, expression, fluency, scenario completion, and overall scores.
- Define score calculation rules.
- Show score history or simple progress indicators.

## PR 13: README, Screenshots, and Demo Video Script

- Update README with final setup and demo steps.
- Add screenshot references.
- Add demo video script and recording checklist.
- Document third-party dependencies, APIs, and AI-generated code usage.
