# Product Design

## Product Positioning

AnytimeSpeak is an AI English speaking practice tool for learners who want realistic, scenario-based conversation training. It focuses on practical speaking confidence, useful corrections, and measurable improvement.

The MVP is designed for a course demo: it should be stable, easy to understand, and reproducible without private credentials.

## Current Product Direction

- Chinese-first UI for navigation, instructions, feedback labels, and demo guidance.
- English-first practice content for role-play replies, recommended expressions, and reusable phrases.
- Session-based scenario coaching rather than isolated single-message chat.
- Static story seeds for each scenario so every session starts with a concrete context.
- Latest-turn feedback that corrects the most recent user message without re-scoring the whole dialogue.
- Score breakdowns for per-turn feedback and post-session review.
- Voice as the main practice entry where supported, with text input as the stable fallback.
- AI reply auto-play through browser speech synthesis when supported.
- User recording replay through browser recording APIs.
- Backend LLM provider mode with deterministic mock fallback.

## Current User Flow

1. Open the app.
2. Optionally create or select a lightweight practice profile when Guest Profile is available.
3. Choose a practice scenario.
4. Read the Chinese story intro and the English story intro for the selected seed.
5. Start the session-based conversation.
6. Speak or type English input.
7. Receive an AI role-play reply; playback may start automatically when supported.
8. Review latest-turn feedback with recommended English, issue explanation, and score breakdown.
9. Replay the user's own recording when available.
10. End the session.
11. Review summary, corrections, suggestions, provider label, and scores.
12. Optionally review saved practice history when Practice History is available and stable.

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

Guest Profile and Practice History are demo-enhancement features, not replacements for the core coaching loop.

Current `main` status:

- Guest Profile is planned / in progress outside current `main`.
- Practice History with SQLite is planned / in progress outside current `main`.
- Current coaching sessions are kept in backend memory for the active practice flow.
- SQLite database files are local runtime artifacts and must stay ignored.

Intended PR13 behavior:

- Guest users create a lightweight nickname profile, with no password or OAuth.
- Completed sessions can be saved with messages, feedback, summary, scores, and provider.
- History list and detail views help users review past practice.
- If save reliability is not fully verified, history should be treated as an optional demo step.

## Future Optimization

- Username and password login for more durable accounts.
- More stable history saving and retry behavior.
- Streaming ASR or cloud speech recognition provider.
- UI and demo polish for layout, loading states, and recording reliability.
- More detailed pronunciation and fluency evaluation.
