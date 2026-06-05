# AGENTS.md

## Project

AnytimeSpeak is an AI English speaking practice project. The MVP focuses on a stable demo loop: choose a scenario, practice a conversation, receive feedback, end the session, and review a scored summary.

## Repository Structure

- `docs/`: project plans, product design, PR plans, demo notes, and decision records.
- `frontend/`: React + Vite + TypeScript app, added in a later PR.
- `backend/`: FastAPI service, added in a later PR.
- `README.md`: public project overview, setup notes, dependencies, demo links, and current status.

## Development Principles

- Do one small feature per PR.
- Do not implement the whole project in one large change.
- Keep `main` runnable after every merge.
- Prefer a complete, stable MVP path over broad unfinished features.
- Use mock mode when API keys are unavailable so the demo remains reproducible.

## PR Rules

Each PR must include:

- Title
- Feature description
- Implementation approach
- Test method
- Third-party libraries, APIs, or AI-generated code used

## Commit Rules

- Use concise conventional commits, for example `docs: add project guidelines and planning documents`.
- Keep commits focused and distributed across the development cycle.
- Avoid mixing unrelated changes in one commit.

## Security

- Never commit API keys, tokens, `.env` files, private credentials, or unauthorized assets.
- Use environment variables for provider configuration.
- Keep mock data free of personal or sensitive information.

## Documentation

- Update `README.md` when adding dependencies, setup steps, major features, or demo instructions.
- Update files under `docs/` when product scope, architecture, scoring rules, or PR plans change.
