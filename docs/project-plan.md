# AnytimeSpeak Project Plan

## Project Background

AnytimeSpeak is a course challenge project focused on AI English speaking practice. The goal is to help learners rehearse realistic English conversations in common scenarios and receive actionable feedback after practice.

The project prioritizes a complete and stable MVP demo over a broad but fragile feature set. The current MVP path includes a React + Vite + TypeScript frontend, a FastAPI backend, session-based scenario coaching, browser speech input/playback, user recording replay, LLM provider mode, and deterministic mock fallback.

## Scope Update

Early planning treated complex cloud accounts and cloud history as Non-MVP. That remains true: username/password login, OAuth, cloud sync, and long-term multi-device history are not required for the core MVP demo.

However, a lightweight Guest Profile plus local SQLite Practice History has been promoted into the demo-enhancement track. On current `main`, the stable source of truth is README Current Status, `docs/api-contract.md`, and current code. If a feature branch or Draft PR has Guest Profile / Practice History work, describe it as in progress until merged. Do not duplicate that work or claim it is implemented on `main` before the API and README confirm it.

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
3. User sends English input. Voice is the preferred supported-browser path; text input remains the stable fallback.
4. AI replies in role according to the selected scenario.
5. The system gives grammar and expression feedback at a reasonable time.
6. User ends the practice.
7. The system generates a post-session summary and quantitative scores.

MVP scenario coverage:

- Interview, Restaurant Ordering, and Meeting remain the core scenarios.
- Additional scenarios may be present when the stable core path still works.
- Each scenario should include static story seeds with Chinese and English intros.

MVP feedback dimensions:

- Grammar
- Expression
- Fluency
- Scenario completion
- Overall score

## Non-MVP Features

The following are valuable but not prioritized before the stable MVP:

- Full pronunciation phoneme-level scoring.
- Full username/password accounts, OAuth, and cloud-synced history.
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
- Text fallback when browser speech features are unavailable

### Backend

- FastAPI
- Python
- Environment-variable based LLM configuration
- Mock response mode when no API key is available
- Backend in-memory sessions for the active coaching flow
- Local SQLite only for lightweight Guest Profile / Practice History when that feature is merged

### AI Layer

- Provider configuration through environment variables.
- Mock mode must keep local demos reproducible.
- Feedback generation should avoid interrupting every turn unless the user requests detailed correction.

### Demo Stability

- Text input remains the fallback path.
- Voice features are progressive enhancements.
- Main demo flow should run without private credentials.
