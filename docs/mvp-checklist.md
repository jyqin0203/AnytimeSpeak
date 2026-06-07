# MVP Checklist

Status labels:

- Done: verified by current `main` code or documentation.
- Pending verification: implemented or expected, but should be checked in the final recording environment.
- Not implemented: planned extension, not part of current `main`.

## Functional Completeness

- [x] Done: User can choose scenario-based practice.
- [x] Done: User can enter a practice page after selecting a scenario.
- [x] Done: Practice session includes a selected story seed and story intro.
- [x] Done: User can send English input by text.
- [x] Done: User can send voice input where browser/provider support is available.
- [x] Done: AI replies according to the selected scenario role.
- [x] Done: Latest-turn feedback is available.
- [x] Done: User can end the practice session.
- [x] Done: User can review a post-session summary.
- [x] Done: User can see quantitative scores after the session.
- [ ] Pending verification: Main demo loop works start to finish in the final recording environment.

## Frontend

- [x] Done: React, Vite, and TypeScript app exists.
- [x] Done: Scenario selection UI includes core and extended scenarios.
- [x] Done: Practice UI shows story, conversation, feedback, input, mic, and end action.
- [x] Done: Feedback is shown without replacing the role-play conversation.
- [x] Done: Summary and score views are readable.
- [x] Done: Text input remains available as stable fallback.
- [x] Done: Login/history UI exists.
- [x] Done: Pronunciation mini panel exists for voice turns.
- [ ] Pending verification: Final screenshots are readable on desktop and mobile-sized browser windows.

## Backend

- [x] Done: FastAPI service exists.
- [x] Done: `/api/health` returns `{"status":"ok"}`.
- [x] Done: `/api/scenarios` returns scenario data with story seed fields.
- [x] Done: `/api/sessions` starts a session with selected story intro and opening message.
- [x] Done: `/api/chat` supports the conversation flow.
- [x] Done: `/api/feedback` supports latest-turn feedback.
- [x] Done: `/api/summary` supports scored post-session summary.
- [x] Done: `/api/asr/mode` and `/ws/asr` support optional Doubao ASR mode.
- [x] Done: `/api/pronunciation/assess` supports pronunciation scoring with fallback.
- [x] Done: `/api/users/*` supports username/password auth.
- [x] Done: `/api/history/*` supports saved practice sessions.
- [ ] Pending verification: Backend error messages are clear enough for final demo troubleshooting.

## Provider And Fallback

- [x] Done: `provider` distinguishes LLM vs backend mock results.
- [x] Done: Backend mock fallback works without API keys.
- [x] Done: Frontend local fallback is separate from backend mock fallback.
- [x] Done: Doubao ASR falls back to browser/text mode when not configured.
- [x] Done: Pronunciation assessment falls back to `heuristic_mock` when not configured or provider fails.
- [ ] Pending verification: LLM provider path works with valid test credentials.
- [ ] Pending verification: Doubao ASR works with valid test credentials.
- [ ] Pending verification: XFYUN pronunciation provider works with valid test credentials.

## Voice Features

- [x] Done: Browser `SpeechRecognition` path exists.
- [x] Done: Text input still works when speech fails.
- [x] Done: Browser `SpeechSynthesis` playback exists.
- [x] Done: AI reply auto-play is supported where browser playback works.
- [x] Done: User recording replay exists through browser recording support.
- [x] Done: Voice turns can show pronunciation assessment.
- [x] Done: Text turns do not show fake pronunciation scores.
- [ ] Pending verification: Speech recognition, playback, and recording replay are stable in the final recording browser.

## Feedback And Summary

- [x] Done: Feedback evaluates the latest user message.
- [x] Done: Feedback includes recommended English.
- [x] Done: Feedback includes issue and explanation.
- [x] Done: Feedback includes grammar, naturalness, relevance, and clarity scores.
- [x] Done: Pronunciation feedback includes pronunciation, fluency, accuracy, completeness, and overall scores.
- [x] Done: Summary includes strengths, repeated issues, better expressions, scenario completion, next focus, and quantitative scores.
- [x] Done: Score scale is 0-100.

## Profile And Practice History

- [x] Done: Username/password registration and login.
- [x] Done: Passwords are salted PBKDF2 hashes.
- [x] Done: SQLite practice history API and UI.
- [x] Done: Completed sessions auto-save to history.
- [x] Done: History list and session detail review.
- [x] Done: Pronunciation assessment can be saved inside feedback JSON.
- [x] Done: SQLite runtime database files are ignored.
- [ ] Pending verification: Save/retry behavior works in final recording environment.

## Documentation

- [x] Done: README is Chinese-first.
- [x] Done: README includes setup, current status, screenshots, API overview, demo steps, dependencies, security, and future work.
- [x] Done: API contract matches implemented endpoints.
- [x] Done: Product design reflects current UI and provider/fallback behavior.
- [x] Done: Demo script describes the final 3-5 minute flow.
- [x] Done: Submission guide exists.
- [ ] Pending verification: Demo video link is added only after a real accessible video exists.

## Security And Hygiene

- [x] Done: `.env` and `.env.*` are ignored except `.env.example`.
- [x] Done: SQLite database files are ignored.
- [x] Done: Node build output and Python caches are ignored.
- [ ] Pending verification: No `.env` is staged or committed.
- [ ] Pending verification: No real API key, token, private credential, or real database file is staged or committed.
- [ ] Pending verification: Screenshots and videos do not expose secrets or private data.
- [ ] Pending verification: Final PR is docs-focused and does not modify core frontend/backend logic.

## Not Implemented

- [ ] Not implemented: Cloud TTS provider endpoint.
- [ ] Not implemented: Cloud-synced multi-device history.
- [ ] Not implemented: Phoneme-level pronunciation visualization.
- [ ] Not implemented: Teacher dashboard.
- [ ] Not implemented: Personalized long-term learning path.
