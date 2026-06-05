# MVP Checklist

Use this checklist before the final MVP submission and before opening or merging release-related PRs.

Current-state note: unchecked items are not claims that the feature already exists. This checklist is a final acceptance tool for the MVP and should be updated only when the implementation actually supports the item.

## Functional Completeness

- [ ] User can choose an MVP scenario: Interview, Restaurant Ordering, or Meeting.
- [ ] User can enter the practice page after selecting a scenario.
- [ ] Practice page shows the selected scenario goal and AI role.
- [ ] User can send English input.
- [ ] AI can reply according to the selected scenario role.
- [ ] User can end the practice session.
- [ ] User can review a post-session summary.
- [ ] User can see quantitative scores after the session.
- [ ] The main demo loop works from start to finish without manual database edits or hidden setup.

## Frontend

- [ ] React, Vite, and TypeScript app starts with the documented command.
- [ ] Scenario selection UI is clear and includes all MVP scenarios.
- [ ] Practice UI shows conversation history in a readable order.
- [ ] User input has loading, disabled, or pending states where needed.
- [ ] Error states are visible and understandable.
- [ ] Feedback is shown without blocking the conversation flow.
- [ ] End-session action is easy to find.
- [ ] Summary and score views are readable on the target demo screen size.
- [ ] Text input remains available as the stable fallback path.

## Backend

- [ ] FastAPI service starts with the documented command.
- [ ] Health endpoint confirms the backend is running.
- [ ] `/api/health` returns `{"status":"ok"}`.
- [ ] Planned endpoints follow `docs/api-contract.md` when implemented.
- [ ] Chat endpoint supports the MVP conversation flow.
- [ ] Feedback or summary endpoints support mock mode when provider keys are unavailable.
- [ ] Environment variables are used for provider configuration.
- [ ] Backend errors return clear messages for the frontend to handle.
- [ ] The backend can run locally without committing private credentials.

## Voice Features

- [ ] Speech input uses browser `SpeechRecognition` only when supported.
- [ ] Unsupported speech recognition has a clear fallback message or disabled state.
- [ ] Recognized speech is editable before sending.
- [ ] Speech recording has clear start and stop controls.
- [ ] Speech playback uses browser `SpeechSynthesis` where available.
- [ ] AI reply playback has play and stop controls.
- [ ] Text input still works when speech features fail or are unavailable.

## Feedback And Summary

- [ ] Per-turn feedback is brief and non-disruptive.
- [ ] Feedback includes grammar correction when there is a clear issue.
- [ ] Feedback includes expression improvement when wording sounds unnatural.
- [ ] Feedback can provide encouragement when the user message is already clear.
- [ ] Post-session summary includes overall performance.
- [ ] Post-session summary includes key strengths.
- [ ] Post-session summary includes repeated grammar issues.
- [ ] Post-session summary includes better expressions to reuse.
- [ ] Post-session summary includes scenario goal completion.
- [ ] Post-session summary includes suggested next practice focus.
- [ ] Scores include grammar, expression, fluency, scenario completion, and overall score.
- [ ] Score scale is 0 to 100.
- [ ] Score weighting follows the documented MVP design or any later documented decision record.

## README

- [ ] README explains the project goal and MVP scope.
- [ ] README includes frontend setup instructions.
- [ ] README includes backend setup instructions.
- [ ] README documents mock mode and how to run without API keys.
- [ ] README lists third-party libraries, frameworks, APIs, and AI-generated code usage.
- [ ] README includes demo instructions or links to demo documentation.
- [ ] README includes the final demo video link before submission.
- [ ] README status matches the current MVP implementation.

## PR And Commit Hygiene

- [ ] Each PR has one focused purpose.
- [ ] Docs-only PRs avoid changes under `frontend/` and `backend/` unless explicitly required.
- [ ] PR title is concise and follows project conventions.
- [ ] PR description includes feature description.
- [ ] PR description includes implementation approach.
- [ ] PR description includes test method.
- [ ] PR description discloses third-party libraries, APIs, and AI-generated code used.
- [ ] Commit messages are concise conventional commits.
- [ ] Commits are focused and do not mix unrelated changes.
- [ ] The PR does not include unrelated generated files or local caches.
- [ ] `main` remains runnable after merge.

## Security

- [ ] No API keys are committed.
- [ ] No tokens are committed.
- [ ] No `.env` files are committed.
- [ ] No private credentials are committed.
- [ ] No unauthorized assets are committed.
- [ ] Mock data does not contain personal or sensitive information.
- [ ] Provider configuration is loaded from environment variables.
- [ ] Demo screenshots and videos do not expose secrets, local credentials, or private account data.

## Demo Video Submission

- [ ] Demo video is 3 to 5 minutes long or close to the required course duration.
- [ ] Demo video introduces the product and MVP goal.
- [ ] Demo video shows scenario selection.
- [ ] Demo video shows a practice conversation.
- [ ] Demo video shows grammar or expression feedback.
- [ ] Demo video shows ending the practice session.
- [ ] Demo video shows the post-session summary.
- [ ] Demo video shows grammar, expression, fluency, scenario completion, and overall scores.
- [ ] Demo video briefly explains frontend, backend, AI configuration, and mock mode.
- [ ] Demo video link is accessible from the final submission location.
- [ ] Demo video does not show API keys, tokens, `.env` files, or private credentials.
