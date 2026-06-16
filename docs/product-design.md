# Product Design

## Product Positioning

AnytimeSpeak is an AI English speaking practice tool for learners who want realistic, scenario-based conversation training. It focuses on practical speaking confidence, useful corrections, measurable progress, and a stable demo path that works without private credentials.

The UI is Chinese-first for navigation, scenario descriptions, feedback labels, and demo readability. English remains the practice language for role-play replies, recommended expressions, reusable phrases, and user speaking output.

## Current Product Experience

- Chinese-first UI with a soft pink/lavender Lover-style visual direction.
- Scenario cards for common real-life contexts such as interview, ordering food, meeting, travel, and daily conversation.
- Session-based scenario coaching instead of isolated single-message chat.
- Static story seeds with Chinese and English intros so each session starts from a concrete situation.
- Compact practice layout with conversation, input, mic control, feedback, and end action in one focused workspace.
- AI role-play replies that stay in scenario and continue the conversation.
- Latest-turn feedback that corrects the newest user message without re-scoring earlier turns.
- Browser speech input, optional Doubao Streaming ASR, browser speech synthesis playback, user recording replay, and text fallback.
- Pronunciation assessment for voice turns only; text turns do not show fake pronunciation scores.
- Username/password login and SQLite-backed history for saved sessions.
- LLM provider mode plus deterministic backend mock fallback.

## Current User Flow

1. Open the app.
2. Register or log in from the topbar, or continue practicing before saving history.
3. Choose a scenario.
4. Read the Chinese and English story intro for the selected seed.
5. Start a session-based conversation.
6. Speak or type English in the composer.
7. Receive an AI role-play reply and optional auto-play.
8. Review latest-turn feedback: recommended English, issue, explanation, natural option, score breakdown, and provider badge.
9. For voice turns, review compact pronunciation feedback when available.
10. Replay the user's own latest recording when browser support allows.
11. End the session.
12. Review post-session summary and scores.
13. Open history to review saved sessions and details.

## Scenario Design

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

Story seeds are hand-written and deterministic. The backend does not ask an LLM to invent a new story per session.

## Feedback Design

Latest-turn feedback is tied to the most recent user message. Previous turns provide context only.

Current feedback includes:

- What the user said.
- Interpreted user intent.
- Recommended English.
- Main issue.
- Why the recommendation is better.
- More natural option.
- Numeric score.
- Score breakdown for grammar, naturalness, relevance, and clarity.
- Provider label and safe fallback reason when available.

## Pronunciation Assessment

Pronunciation assessment is a separate module from grammar/expression feedback. It appears for voice turns and stays compact so it does not interrupt the conversation.

Current pronunciation feedback includes:

- Overall pronunciation score.
- Pronunciation, fluency, accuracy, completeness, and optional rhythm scores.
- Chinese feedback and improvement tips.
- Word-level tips when the fallback/provider can infer useful targets.
- Provider and `is_fallback` state.

The backend supports local heuristic scoring for stable demos and optional iFlytek/XFYUN ISE scoring when credentials are configured. Provider failures fall back to the heuristic result.

## Post-Session Summary

The summary includes:

- Overall performance.
- Key strengths.
- Repeated issues.
- Better expressions to reuse.
- Scenario goal completion.
- Suggested next practice focus.
- Quantitative scores.
- Provider label.

Scores use a 0-100 scale:

- Grammar.
- Expression.
- Fluency.
- Scenario completion.
- Overall.

## Voice Interaction

- Browser `SpeechRecognition` is the default speech input path when supported.
- Doubao Streaming ASR is available through `/ws/asr` when `ASR_PROVIDER_MODE=doubao` and backend credentials are configured.
- Text input is always available and is the stable fallback.
- Browser `SpeechSynthesis` plays AI replies where supported.
- Browser recording APIs support user recording replay and pronunciation upload where available.

## Profile And History

Practice history is implemented on `main`.

- Username/password registration and login from the topbar.
- Passwords are salted PBKDF2 hashes, never plaintext.
- Completed sessions are saved to SQLite.
- Messages, feedback, summary, scores, provider labels, and pronunciation assessment JSON can be reviewed later.
- If save fails, the frontend keeps a pending session and shows a fallback note.
- `backend/data/*.db` files are runtime artifacts and are ignored by git.

## Future Optimization

- Cloud TTS provider for lower-latency voice output.
- Phoneme-level pronunciation feedback, stress, rhythm, and visual follow-reading.
- More durable cloud history and multi-device sync.
- Personalized learning path and long-term ability curve.
- More scenarios, difficulty levels, and reusable expression review.
