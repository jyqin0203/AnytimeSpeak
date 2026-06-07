# Demo Script

This script is designed for a 3 to 5 minute MVP demo video. The goal is to show the current AnytimeSpeak loop clearly: choose a scenario, read the story intro, practice a conversation, receive latest-turn feedback, end the session, and review a scored summary.

## Recording Setup

- Use backend mock fallback if LLM credentials are unavailable.
- Keep text input ready as the stable fallback path.
- Use speech input, AI auto-play, and user recording replay only if the browser supports them reliably during recording.
- Do not show API keys, tokens, `.env` files, private credentials, or real personal data.
- Record a single complete session from scenario selection to post-session summary.
- Treat Guest Profile and Practice History as optional demo steps unless they are stable on the branch being recorded.

## Suggested Timing

| Section | Time |
| --- | --- |
| Opening introduction | 20 to 30 seconds |
| Optional profile setup | 15 to 30 seconds |
| Scenario and story intro | 30 to 45 seconds |
| Speaking practice | 60 to 90 seconds |
| Latest-turn feedback | 45 to 60 seconds |
| Post-session summary and scores | 45 to 60 seconds |
| Optional history review | 20 to 30 seconds |
| Technical architecture | 30 to 45 seconds |
| Closing summary | 15 to 30 seconds |

## 1. Opening Introduction

Show the scenario selection or current first screen.

Suggested narration:

> Hi, this is AnytimeSpeak, an AI English speaking practice tool. The current MVP helps learners practice scenario-based English conversations, receive latest-turn feedback, and review a scored summary after each session. The UI is Chinese-first, while the role-play conversation and recommended expressions stay in English.

Key points to mention:

- The product is for English speaking practice.
- The demo can run without private API keys through backend mock fallback.
- Text input remains available when speech APIs are unavailable.

## 2. Optional Profile Setup

Only include this section if Guest Profile is stable on the branch being recorded.

Recommended action:

1. Create or select a lightweight practice profile with a nickname.
2. Mention that this is not username/password login.
3. Avoid entering real personal information.

Suggested narration:

> If profile support is enabled, the learner can create a lightweight guest profile with a nickname. This is only for demo practice history, not a full account system.

If the feature is not stable, skip it without narration.

## 3. Scenario And Story Intro

Show the scenario selection area and briefly introduce available scenarios.

Recommended action:

1. Point out Interview, Restaurant Ordering, and Meeting.
2. Select one scenario, for example Interview or Meeting.
3. Show the selected story intro in Chinese and English.
4. Start the practice session.

Suggested narration:

> Each scenario has static story seeds, so the learner starts with a concrete situation instead of a generic chat. The selected session shows a Chinese story intro, an English intro, and an opening message from the AI role.

## 4. Speaking Practice

Show the practice page with the AI opening message.

Recommended sample user response:

> Hello, thank you for meeting with me. I am interested in this role because I have experience working with web applications and I enjoy solving user problems.

Recommended action:

1. Use speech input if it is stable in the recording browser.
2. If speech recognition is not stable, type the sample response.
3. Send the response.
4. Let the AI reply and show auto-play if it works.
5. Send one more response with a small grammar or expression issue.

Recommended second user response:

> I worked in a team project before and I was responsible to build the frontend page.

Suggested narration:

> The conversation is session-based, so the backend receives the selected scenario, the latest user message, and the previous turns. The AI reply stays in role and continues the practice conversation.

## 5. Latest-Turn Feedback

Show the feedback panel for the most recent user message.

Suggested narration:

> Feedback focuses on the latest user turn. The previous dialogue is used as context, but the system does not re-score every earlier message. The feedback includes recommended English, the main issue, an explanation, and a score breakdown.

Example feedback to highlight:

- "responsible to build" can be improved to "responsible for building".
- "frontend page" may sound more natural as "frontend interface" or "frontend features".
- The score breakdown includes grammar, naturalness, relevance, and clarity.
- The provider badge shows whether the result came from LLM mode or backend mock fallback.

If user recording replay is stable, briefly replay the user's latest recording. If it is not stable, skip this step.

## 6. Post-Session Summary And Scores

Click the end-practice action and show the summary screen.

Suggested narration:

> After the learner ends the practice, AnytimeSpeak generates a post-session summary. It reviews strengths, repeated issues, reusable expressions, scenario completion, and a next practice focus.

Highlight these summary fields:

- Overall performance summary.
- Key strengths.
- Repeated issues.
- Better expressions to reuse.
- Scenario goal completion.
- Suggested next practice focus.
- Provider badge.

Then show the score area.

Suggested narration:

> The summary also shows quantitative scores from 0 to 100 for grammar, expression, fluency, scenario completion, and overall performance.

## 7. Optional History Review

Only include this section if Practice History is stable on the branch being recorded.

Recommended action:

1. Open the history view.
2. Show the saved session list.
3. Open one session detail view.
4. Point out dialogue, feedback, summary, scores, and provider.

Suggested narration:

> If practice history is enabled, completed sessions can be saved locally and reviewed later. This is a demo enhancement; full username/password login and cloud history are future work.

If save reliability is not verified, skip this section or say it is under active iteration.

## 8. Technical Architecture Summary

Show the repository structure, README, or an architecture slide if available.

Suggested narration:

> The frontend is built with React, Vite, and TypeScript. The backend uses FastAPI and Python. Coaching endpoints support an LLM provider when environment variables are configured, and deterministic backend mock fallback when provider mode or credentials are unavailable.

Key architecture points:

- Current coaching endpoints include `/api/scenarios`, `/api/sessions`, `/api/chat`, `/api/feedback`, and `/api/summary`.
- Backend mock fallback is different from frontend local fallback. Backend mock means the backend answered successfully with deterministic coaching. Frontend local fallback means the browser could not use the backend response and kept the demo moving locally.
- Browser `SpeechRecognition` is used where supported for speech input.
- Browser `SpeechSynthesis` is used for AI reply playback.
- Browser recording APIs support user recording replay where available.
- API keys and `.env` contents must not be shown.

## 9. Closing Summary

Return to the summary screen or completed demo loop.

Suggested narration:

> This demo shows the current AnytimeSpeak MVP loop: choose a scenario, read a story intro, practice by voice or text, get latest-turn feedback, end the session, and review a scored summary. Next improvements include more stable history, username/password login, streaming ASR, and UI polish.

Final checklist before stopping the recording:

- The selected scenario and story intro are visible.
- At least one user message and one AI reply are visible.
- Latest-turn feedback is visible and easy to understand.
- The session summary and scores are visible.
- Optional history is shown only if stable.
- No API key, token, `.env` content, or private credential appears in the recording.
