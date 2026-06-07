# Demo Script

This script is for a 3-5 minute final demo video. Use mock mode or test credentials. Do not show `.env`, API keys, tokens, provider consoles, real database contents, or private account data.

## Recording Setup

- Use `LLM_PROVIDER_MODE=mock` unless a test LLM key is configured and safe to use.
- Keep text input ready as the stable fallback.
- Use speech input, Doubao ASR, AI auto-play, pronunciation assessment, and recording replay only when they are stable in the recording browser.
- Use a test account such as `demo_user`; do not use a personal username/password.
- Record one complete loop from scenario selection to summary and history.

## Suggested Timing

| Section | Time |
| --- | --- |
| Product intro | 20-30 seconds |
| Login or test account | 15-25 seconds |
| Scenario and story seed | 30-45 seconds |
| Practice conversation | 60-90 seconds |
| Feedback and pronunciation | 45-60 seconds |
| Summary and scores | 45-60 seconds |
| History and architecture | 30-45 seconds |
| Closing | 10-20 seconds |

## Required Demo Flow

1. Show the home/scenario page.
2. Briefly explain AnytimeSpeak: AI English speaking practice for real scenarios.
3. Register or log in with a test user.
4. Select a scenario, for example Interview or Meeting.
5. Show the Chinese and English story intro.
6. Send one voice or text response.
7. Let the AI reply.
8. Send a second response with a small expression issue.
9. Show latest-turn feedback and provider badge.
10. If voice was used, show pronunciation assessment and optional recording replay.
11. End practice.
12. Show summary, reusable expressions, and score breakdown.
13. Open history and show the saved session list/detail.

## Sample Narration

Opening:

> This is AnytimeSpeak, an AI English speaking practice tool. Learners choose a real scenario, practice a conversation with an AI role, receive expression feedback, and finish with a scored summary. The UI is Chinese-first, while the practice content stays in English.

Scenario:

> Each scenario includes static story seeds, so the learner starts from a concrete situation instead of a generic chat. This also keeps demo behavior reproducible.

Practice:

> The conversation is session-based. The backend receives the selected scenario, the latest user message, and previous turns, then returns a role-play reply and feedback. If LLM credentials are missing, backend mock fallback still returns a complete response.

Feedback:

> Feedback focuses on the latest user turn. It recommends a better English expression, explains why, gives a natural alternative, and shows grammar, naturalness, relevance, and clarity scores.

Pronunciation:

> Voice turns can also show pronunciation assessment. Without external credentials, the backend uses a heuristic fallback. With XFYUN credentials, it can call the provider from the backend without exposing secrets to the browser.

Summary:

> At the end, AnytimeSpeak summarizes strengths, repeated issues, better expressions, scenario completion, next practice focus, and quantitative scores.

History:

> After login, completed sessions are saved to local SQLite and can be reviewed later.

Architecture:

> The frontend is React, Vite, and TypeScript. The backend is FastAPI. LLM, ASR, and pronunciation providers are configured with environment variables, while mock fallback keeps the demo reproducible without keys.

## Optional Items

- Doubao ASR live transcript if credentials and network are stable.
- AI reply auto-play if browser speech synthesis behaves reliably.
- User recording replay if browser permissions and recording output are stable.
- XFYUN pronunciation provider if test credentials are configured.

Skip optional items silently if they are unstable. Do not claim optional provider mode is active unless the provider badge or local setup confirms it.

## Final Checks Before Recording

- No `.env`, API key, token, or provider console is visible.
- No real personal account or real history record is shown.
- The selected scenario and story intro are visible.
- At least one user message and one AI reply are visible.
- Feedback and summary scores are readable.
- Demo video link remains `TBD` until a real accessible link exists.
