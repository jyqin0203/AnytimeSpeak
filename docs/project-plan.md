# AnytimeSpeak Project Plan

## Project Background

AnytimeSpeak is a course challenge project focused on AI English speaking practice. The goal is to help learners rehearse realistic English conversations in common scenarios and receive actionable feedback after practice.

The project prioritizes a complete and stable MVP demo over a broad but fragile feature set. The first version will support text input as the reliable baseline, then add browser-based speech input and speech playback.

## Topic Requirements

- Support scenario selection, such as interview, restaurant ordering, and meeting conversations.
- Support real-time or near-real-time voice conversation.
- Support pronunciation evaluation or fluency feedback.
- Support grammar correction and expression improvement suggestions.
- Support post-session summaries.
- Show measurable improvement feedback, such as grammar score, expression score, fluency score, and overall score.

## Evaluation Rules

### Completeness and Innovation: 40%

- Product design is reasonable.
- Core functions are complete.
- Interaction is smooth.
- The experience includes useful and creative ideas.

### Development Process and Quality: 40%

- Architecture is clear and reasonable.
- Code is robust, readable, and maintainable.
- Logic is well organized.
- PR quantity and quality are reasonable.
- Commits are distributed across the development period.

### Demo and Presentation: 20%

- Demo video is clear and complete.
- The presentation explains the product, workflow, and value clearly.
- The demo can reproduce the main feature loop reliably.

## Submission Rules

- Submit a public GitHub or Gitee repository.
- Submit a demo video link.
- Submit a README document.
- Keep continuous PRs and commits. Do not import all code on the final day.
- Each PR should do one thing and stay small.
- PR descriptions must include title, feature description, implementation approach, and test method.
- The `main` branch must remain runnable after merge.
- Third-party libraries, frameworks, APIs, or AI-generated code must be documented in README and PR descriptions.
- Do not commit API keys, private credentials, unauthorized materials, or infringing assets.
- The repository must be created after project kickoff, and commit timestamps must fall within the development period.

## MVP Scope

The MVP should deliver this complete loop:

1. User selects a practice scenario.
2. User enters a practice page.
3. User sends English input. Text input is supported first, speech input is added later.
4. AI replies in role according to the selected scenario.
5. The system gives grammar and expression feedback at a reasonable time.
6. User ends the practice.
7. The system generates a post-session summary and quantitative scores.

MVP scenarios:

- Interview
- Restaurant ordering
- Meeting

MVP feedback dimensions:

- Grammar
- Expression
- Fluency
- Scenario completion
- Overall score

## Non-MVP Features

The following are valuable but not prioritized before the stable MVP:

- Full pronunciation phoneme-level scoring.
- Long-term user accounts and cloud history.
- Payment or subscription features.
- Multi-user conversation rooms.
- Native mobile apps.
- Teacher dashboard.
- Advanced learning path recommendation.
- Fine-tuned speech models.
- Real-time interruption and barge-in handling.

## Initial Technical Approach

### Frontend

- React
- Vite
- TypeScript
- Browser `SpeechRecognition` for speech input where supported
- Browser `SpeechSynthesis` for speech playback
- `localStorage` or mock data for MVP session history

### Backend

- FastAPI
- Python
- Environment-variable based LLM configuration
- Mock response mode when no API key is available

### AI Layer

- Provider configuration through environment variables.
- Mock mode must keep local demos reproducible.
- Feedback generation should avoid interrupting every turn unless the user requests detailed correction.

### Demo Stability

- Text input remains the fallback path.
- Voice features are progressive enhancements.
- Main demo flow should run without private credentials.
