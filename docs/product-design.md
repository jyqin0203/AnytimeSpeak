# Product Design

## Product Positioning

AnytimeSpeak is an AI English speaking practice tool for learners who want realistic, scenario-based conversation training. It focuses on practical speaking confidence, useful corrections, and measurable improvement.

The MVP is designed for a course demo: it should be stable, easy to understand, and reproducible without private credentials.

## Current Product Direction

- Chinese-first UI for navigation, instructions, feedback labels, scenario difficulty tags, and focus tags.
- English-first practice content for role-play replies, recommended expressions, and reusable phrases.
- Session-based scenario coaching rather than isolated single-message chat.
- Static story seeds for each scenario so every session starts with a concrete context.
- Latest-turn feedback that corrects the most recent user message without re-scoring the whole dialogue.
- Score breakdowns for per-turn feedback and post-session review.
- Fixed viewport-height practice layout so conversation, voice input, and end button are always visible without scrolling.
- Compact single-row chat composer: text input on the left, small mic button on the right, send button.
- Voice input in English (`en-US`) only; no language toggle.
- AI reply text sanitized to remove em dashes before display.
- Scenarios sorted by difficulty level with beginner (`入门`) first.
- AI reply auto-play through browser speech synthesis when supported.
- User recording replay through browser recording APIs.
- Backend LLM provider mode with deterministic mock fallback.
- Optional Doubao Streaming ASR through a backend WebSocket relay.
- Pronunciation assessment for voice turns with compact score feedback, heuristic fallback, and optional iFlytek/XFYUN ISE provider.

## Current User Flow

1. Open the app.
2. Optionally log in or register from the topbar.
3. Choose a practice scenario (sorted beginner first).
4. Read the Chinese story intro and the English story intro for the selected seed.
5. Start the session-based conversation.
6. Speak or type English input in the chat composer; mic button starts/stops voice input.
7. Receive an AI role-play reply (sanitized text; playback may start automatically when supported).
8. Review latest-turn feedback with recommended English, issue explanation, and score breakdown.
8a. For voice turns, review a compact pronunciation assessment when available. Text turns show no pronunciation score.
9. Replay the user's own recording when available.
10. End the session.
11. Review summary — scores show `—` while loading, then display the final values.
12. Optionally review saved practice history in `练习历史`.

## Scenario Design

The product is no longer only an early three-card MVP plan. The stable scenarios still include Interview, Restaurant Ordering, and Meeting, but the current scenario model also supports richer scenario metadata and additional scenarios.

Each scenario includes:

- English and Chinese titles.
- AI role and learner role.
- Practice goal.
- Multiple static story seeds.
- Chinese and English story intros.
- Opening message.
- Conversation style.
- Feedback focus.
- Useful expressions.

Story seeds should be hand-written and deterministic. The backend should not ask an LLM to invent a new story per session.

## Feedback Design

### Latest-Turn Feedback

Feedback is tied to the latest user message. Previous turns provide context only.

Current feedback includes:

- What the user said.
- Interpreted user intent.
- Recommended English.
- Main issue.
- Explanation of why the recommendation is better.
- More natural option.
- Numeric score.
- Score breakdown for grammar, naturalness, relevance, and clarity.
- `provider` label showing whether the backend used LLM or mock fallback.

### Pronunciation Assessment

Pronunciation assessment is a separate module from grammar/expression feedback. It appears for voice turns only and stays compact so it does not interrupt the conversation loop.

Current pronunciation feedback includes:

- Overall pronunciation score.
- Fluency, accuracy, and completeness scores.
- One or two Chinese improvement tips.
- Provider and fallback handling in the backend response.
- Text-input no-assessment state instead of fake pronunciation scores.

The backend supports local heuristic scoring for stable demos and optional iFlytek/XFYUN ISE scoring when credentials are configured. Provider failures fall back to the heuristic result.

### Post-Session Summary

The post-session summary should include:

- Overall performance summary.
- Key strengths.
- Repeated issues.
- Better expressions the user can reuse.
- Scenario goal completion.
- Suggested next practice focus.
- Quantitative scores.
- `provider` label.

## Scoring Design

Scores use a 0 to 100 scale. Current scoring can come from the LLM provider or deterministic mock rules.

Post-session score dimensions:

- Grammar.
- Expression.
- Fluency.
- Scenario completion.
- Overall.

Initial weighting:

- Grammar: 25%.
- Expression: 25%.
- Fluency: 20%.
- Scenario completion: 30%.

Latest-turn feedback uses:

- Grammar.
- Naturalness.
- Relevance.
- Clarity.

## Voice Interaction Design

### Speech Input

- Use browser `SpeechRecognition` when available.
- Use Doubao Streaming ASR through `/ws/asr` when `ASR_PROVIDER_MODE=doubao` and credentials are configured.
- Treat voice as the primary practice action in supported browsers.
- Let users start and stop recognition manually.
- Convert recognized speech into editable text before sending.
- Show clear fallback behavior when speech recognition is unavailable.

### Speech Playback

- Use browser `SpeechSynthesis` for AI replies.
- Provide play and stop controls.
- Support AI auto-play when available and enabled.

### User Recording Replay

- Use browser recording APIs where available.
- Let users replay their own latest recording for self-review.
- Keep replay optional because browser support and permission behavior can vary.

### Text Fallback

Text input is always available. It is the required stable fallback and ensures the demo works even when speech APIs are unavailable or unstable.

## Profile And History

Practice history is implemented and available on `main`.

Current status:

- Username/password registration and login from the topbar.
- Completed sessions auto-saved after each practice ends (messages, feedback, summary, scores, provider label).
- Pronunciation assessment is saved inside per-turn feedback JSON when available, so history detail can show the score without a database schema migration.
- `练习历史` list and session detail views.
- If save fails, the completed session remains in frontend state as a pending save; summary page shows a fallback note.
- Passwords are stored with salted PBKDF2 hashes, never as plaintext.
- SQLite database file (`backend/data/anytimespeak.db`) is a local runtime artifact, not committed.

## Future Optimization

- More stable history saving and retry behavior.
- UI and demo polish for layout, loading states, and recording reliability.
- Cloud TTS provider for voice output.
- More detailed pronunciation and fluency evaluation after the current compact scoring module is stable.
