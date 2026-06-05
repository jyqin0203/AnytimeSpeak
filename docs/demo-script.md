# Demo Script

This script is designed for a 3 to 5 minute MVP demo video. The goal is to show the complete AnytimeSpeak loop clearly: choose a scenario, practice a conversation, receive feedback, end the session, and review a scored summary.

## Recording Setup

- Use mock mode if API keys are unavailable.
- Keep text input ready as the stable fallback path.
- Use speech input and playback only if the browser supports them reliably during recording.
- Record a single complete session from scenario selection to post-session summary.
- Avoid using personal information in sample conversation messages.

## Suggested Timing

| Section | Time |
| --- | --- |
| Opening introduction | 20 to 30 seconds |
| Scenario selection | 30 to 45 seconds |
| Speaking practice | 60 to 90 seconds |
| Grammar and expression feedback | 45 to 60 seconds |
| Post-session summary and scores | 45 to 60 seconds |
| Technical architecture | 30 to 45 seconds |
| Closing summary | 15 to 30 seconds |

## 1. Opening Introduction

Show the app landing or scenario selection screen.

Suggested narration:

> Hi, this is AnytimeSpeak, an AI English speaking practice tool. The MVP helps learners practice realistic conversations in common scenarios, receive grammar and expression feedback, and review a scored summary after each session. The demo focuses on a stable practice loop that can run in mock mode without private API keys.

Key points to mention:

- The product is for English speaking practice.
- The MVP prioritizes a complete and reproducible demo flow.
- Text input is the reliable baseline, with voice features as progressive enhancements.

## 2. Scenario Selection Demo

Show the scenario selection area and briefly introduce the available scenarios.

Suggested narration:

> First, the learner chooses a practice scenario. The MVP includes interview practice, restaurant ordering, and meeting conversations. Each scenario defines the AI role, the learner role, and a practical goal.

Recommended action:

1. Point out the three MVP scenarios.
2. Select the Interview scenario.
3. Mention the AI role and practice goal before starting.

Suggested narration after selecting Interview:

> I will choose Interview. In this scenario, the AI acts as a hiring manager, and the learner practices introducing themselves, explaining experience, and asking professional follow-up questions.

## 3. Speaking Practice Demo

Show the practice page with the AI opening message.

Suggested narration:

> The practice page starts with a role-play opening line. The learner can type a response, and when supported by the browser, they can also use speech recognition to convert spoken English into editable text.

Recommended sample user response:

> Hello, thank you for meeting with me. I am interested in this role because I have experience working with web applications and I enjoy solving user problems.

Recommended action:

1. Send the sample response.
2. Show the AI role-play reply.
3. Send one more response with a small grammar or expression issue so the feedback area has something useful to show.

Recommended second user response:

> I worked in a team project before and I was responsible to build the frontend page.

Suggested narration:

> The AI continues the conversation in the selected role. The goal is not only to chat, but to help the learner practice realistic communication for the scenario.

## 4. Grammar And Expression Feedback Demo

Show the feedback area or per-turn correction area.

Suggested narration:

> AnytimeSpeak provides lightweight feedback during practice. The feedback should be brief so it does not interrupt the role-play conversation too much.

Example feedback to highlight:

- Grammar: "responsible to build" can be improved to "responsible for building".
- Expression: "frontend page" may sound more natural as "frontend interface" or "frontend features".
- Encouragement: The answer is clear and relevant to the interview scenario.

Suggested narration:

> Here, the learner receives a grammar correction and a more natural expression. The feedback is actionable and connected to the sentence they just used.

If speech features are available, briefly show:

- Start recording.
- Convert speech to text.
- Edit the recognized text if needed.
- Play or stop an AI reply with browser speech synthesis.

If speech features are not available, say:

> For demo stability, text input remains available even when browser speech recognition is not supported.

## 5. Post-Session Summary And Scores Demo

Click the end-practice action and show the summary screen.

Suggested narration:

> After the learner ends the practice, AnytimeSpeak generates a post-session summary. This gives the learner a clear review of strengths, repeated issues, useful expressions, and the next practice focus.

Highlight these summary fields:

- Overall performance summary.
- Key strengths.
- Repeated grammar issues.
- Better expressions to reuse.
- Scenario goal completion.
- Suggested next practice focus.

Then show the score area.

Suggested narration:

> The MVP also shows quantitative scores from 0 to 100. The scoring dimensions are grammar, expression, fluency, scenario completion, and overall performance.

Mention the initial weighting:

- Grammar: 25%.
- Expression: 25%.
- Fluency: 20%.
- Scenario completion: 30%.

Suggested narration:

> These scores make progress visible. In text-only mode, fluency can be estimated from message completeness and communication smoothness. In speech mode, it can later include pauses, restarts, and recognition confidence.

## 6. Technical Architecture Summary

Show the repository structure, README, or an architecture slide if available.

Suggested narration:

> The frontend is built with React, Vite, and TypeScript. The backend uses FastAPI and Python. AI provider configuration is handled through environment variables, and mock mode keeps the demo reproducible when API keys are unavailable.

Key architecture points:

- Frontend handles scenario selection, practice UI, speech input, speech playback, feedback display, and summary review.
- Backend provides health, chat, feedback, and summary endpoints as the MVP grows.
- Browser `SpeechRecognition` is used where supported for speech input.
- Browser `SpeechSynthesis` is used for AI reply playback.
- Mock mode is required for stable local demos without private credentials.

## 7. Closing Summary

Return to the summary screen or show the completed demo loop.

Suggested narration:

> This demo shows the complete AnytimeSpeak MVP loop: select a scenario, practice a realistic conversation, receive grammar and expression feedback, end the session, and review a scored summary. The next improvements can refine voice quality, scoring rules, and feedback accuracy, while keeping the stable text-based practice loop available.

Final checklist before stopping the recording:

- The selected scenario is visible.
- At least one user message and one AI reply are visible.
- Feedback is visible and easy to understand.
- The session summary and scores are visible.
- No API key, token, `.env` content, or private credential appears in the recording.
