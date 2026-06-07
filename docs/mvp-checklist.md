# MVP Checklist

Use this checklist before the final MVP submission and before opening or merging release-related PRs.

Status labels:

- Done: verified by current `main` code or documentation.
- Pending verification: implemented or expected, but should be checked in the target demo browser/environment.
- Not in current main: planned or in a Draft PR, not part of current `main`.

## Functional Completeness

- [x] Done: User can choose scenario-based practice.
- [x] Done: User can enter the practice page after selecting a scenario.
- [x] Done: Practice session includes a selected story seed and story intro.
- [x] Done: User can send English input by text.
- [x] Done: AI can reply according to the selected scenario role.
- [x] Done: Latest-turn feedback is available.
- [x] Done: User can end the practice session.
- [x] Done: User can review a post-session summary.
- [x] Done: User can see quantitative scores after the session.
- [ ] Pending verification: Main demo loop works from start to finish in the recording environment without hidden setup.

## Frontend

- [x] Done: React, Vite, and TypeScript app exists.
- [x] Done: Scenario selection UI includes the core MVP scenarios.
- [x] Done: Practice UI shows conversation history.
- [x] Done: Feedback is shown without replacing the role-play conversation.
- [x] Done: End-session action and summary view exist.
- [x] Done: Text input remains available as the stable fallback path.
- [ ] Pending verification: Loading, disabled, and error states are clear in the final demo path.
- [ ] Pending verification: Summary and score views are readable on the target demo screen size.

## Backend

- [x] Done: FastAPI service exists.
- [x] Done: `/api/health` returns `{"status":"ok"}`.
- [x] Done: `/api/scenarios` returns scenario data with story seed fields.
- [x] Done: `/api/sessions` starts a session with selected story intro and opening message.
- [x] Done: `/api/chat` supports the MVP conversation flow.
- [x] Done: `/api/feedback` supports latest-turn feedback.
- [x] Done: `/api/summary` supports scored post-session summary.
- [x] Done: Coaching endpoints support LLM provider mode and backend mock fallback.
- [x] Done: Environment variables are used for provider configuration.
- [x] Done: Backend can run locally without committing private credentials.
- [ ] Pending verification: Backend errors are clear enough for final demo troubleshooting.

## Provider And Fallback

- [x] Done: `provider` distinguishes `"llm"` from backend `"mock"` results.
- [x] Done: `fallback_reason` can explain backend mock fallback without exposing secrets.
- [x] Done: Frontend local fallback is separate from backend mock fallback.
- [ ] Pending verification: Provider badges/status text are legible in the final demo.
- [ ] Pending verification: LLM provider path works when valid credentials are configured.
- [x] Done: Mock fallback keeps the demo reproducible without API keys.

## Voice Features

- [x] Done: Speech input uses browser `SpeechRecognition` where supported.
- [x] Done: Text input still works when speech features fail or are unavailable.
- [x] Done: Speech playback uses browser `SpeechSynthesis` where supported.
- [x] Done: AI reply auto-play is supported where browser playback works.
- [x] Done: User recording replay exists through browser recording support.
- [ ] Pending verification: Speech recognition works reliably in the recording browser.
- [ ] Pending verification: AI auto-play works reliably in the recording browser.
- [ ] Pending verification: User recording replay works reliably in the recording browser.

## Feedback And Summary

- [x] Done: Per-turn feedback evaluates the latest user message.
- [x] Done: Feedback includes recommended English.
- [x] Done: Feedback includes issue and explanation fields.
- [x] Done: Feedback includes score breakdown for grammar, naturalness, relevance, and clarity.
- [x] Done: Post-session summary includes overall performance.
- [x] Done: Post-session summary includes key strengths.
- [x] Done: Post-session summary includes repeated issues.
- [x] Done: Post-session summary includes better expressions to reuse.
- [x] Done: Post-session summary includes scenario goal completion.
- [x] Done: Post-session summary includes suggested next practice focus.
- [x] Done: Scores include grammar, expression, fluency, scenario completion, and overall score.
- [x] Done: Score scale is 0 to 100.

## Guest Profile And Practice History

- [ ] Not in current main: Guest Profile API and UI.
- [ ] Not in current main: SQLite Practice History API and UI.
- [ ] Not in current main: Auto-save completed sessions to history.
- [ ] Not in current main: History list and session detail review.
- [x] Done: SQLite runtime database files are ignored by `.gitignore`.
- [ ] Pending verification: If PR13 or another branch is used for demo recording, verify profile/history save and retry behavior before showing it.

## README

- [x] Done: README explains the project goal and MVP scope.
- [x] Done: README includes frontend setup instructions.
- [x] Done: README includes backend setup instructions.
- [x] Done: README documents mock mode and how to run without API keys.
- [x] Done: README lists third-party libraries, frameworks, APIs, and AI-generated code usage.
- [x] Done: README includes links to demo documentation.
- [ ] Pending verification: README status matches the exact branch used for final submission.
- [ ] Pending verification: README demo video link is added only after a real video link exists.

## PR And Commit Hygiene

- [ ] Pending verification: Each PR has one focused purpose.
- [ ] Pending verification: Docs-only PRs avoid changes under `frontend/` and `backend/` unless explicitly required.
- [ ] Pending verification: PR title is concise and follows project conventions.
- [ ] Pending verification: PR description includes feature description.
- [ ] Pending verification: PR description includes implementation approach.
- [ ] Pending verification: PR description includes test method.
- [ ] Pending verification: PR description discloses third-party libraries, APIs, and AI-generated code used.
- [ ] Pending verification: Commit messages are concise conventional commits.
- [ ] Pending verification: The PR does not include unrelated generated files or local caches.
- [ ] Pending verification: `main` remains runnable after merge.

## Security

- [x] Done: `.env` and `.env.*` are ignored except `.env.example`.
- [x] Done: SQLite database files (`*.db`, `*.sqlite`, `*.sqlite3`) are ignored.
- [ ] Pending verification: No API keys are committed.
- [ ] Pending verification: No tokens are committed.
- [ ] Pending verification: No `.env` files are committed.
- [ ] Pending verification: No private credentials are committed.
- [ ] Pending verification: No unauthorized assets are committed.
- [ ] Pending verification: Demo screenshots and videos do not expose secrets, local credentials, private account data, or `.env` contents.

## Demo Video Submission

- [ ] Pending verification: Demo video is 3 to 5 minutes long or close to the required course duration.
- [ ] Pending verification: Demo video introduces the product and MVP goal.
- [ ] Pending verification: Demo video shows scenario selection.
- [ ] Pending verification: Demo video shows the session story intro.
- [ ] Pending verification: Demo video shows a practice conversation.
- [ ] Pending verification: Demo video shows speech input/playback or clearly uses text fallback.
- [ ] Pending verification: Demo video shows grammar or expression feedback.
- [ ] Pending verification: Demo video shows ending the practice session.
- [ ] Pending verification: Demo video shows the post-session summary.
- [ ] Pending verification: Demo video shows grammar, expression, fluency, scenario completion, and overall scores.
- [ ] Pending verification: Demo video briefly explains frontend, backend, LLM provider mode, backend mock fallback, and frontend local fallback.
- [ ] Pending verification: Demo video link is accessible from the final submission location.
- [ ] Pending verification: Demo video does not show API keys, tokens, `.env` files, database files, or private credentials.
