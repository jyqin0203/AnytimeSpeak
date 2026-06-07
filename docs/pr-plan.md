# PR Plan

This project should be developed through small, focused PRs. Each PR should keep `main` runnable and include a clear description, implementation approach, test method, and dependency/API disclosure.

## Current Status Source Of Truth

The early PR numbering below is a planning history, not a guaranteed statement of what is currently missing. When PR numbering conflicts with the current implementation state, use these sources in this order:

1. Current code on `main`.
2. README Current Status.
3. `docs/api-contract.md` current implemented sections.

Do not re-implement a feature just because an early numbered PR title mentions it. First check whether it is already merged, in a Draft PR, or superseded by a later implementation.

## Agent PR Submission Guide

This section is the canonical PR workflow for Codex/Coding Agents working on this repository. Follow it before opening any future PR.

### Required Tools

Use local Git for branch, commit, and push. On this Windows machine, Git is available through the absolute path below, while GitHub CLI is not currently installed or available through `PATH`.

```powershell
& 'C:\Program Files\Git\cmd\git.exe' --version
```

Current local checks from this machine:

```powershell
where.exe gh
Test-Path 'C:\Program Files\GitHub CLI\gh.exe'
Test-Path 'C:\Program Files (x86)\GitHub CLI\gh.exe'
Test-Path "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
```

Expected current result: no `gh` executable is found.

Codex GitHub plugin is enabled in this user's Codex config:

```powershell
# C:\Users\86183\.codex\config.toml
[plugins."github@openai-curated"]
enabled = true
```

However, plugin installation does not guarantee that the GitHub connector tool is exposed inside an already-running Codex session. If the connector tool is not visible to the agent, start a new Codex session after installing/enabling the plugin, then ask the agent to create the PR from the already-pushed branch.

If GitHub CLI is preferred, install `gh`, make sure it is on `PATH` or document its absolute path, then authenticate it with `gh auth login`.

### Start From Remote Main

Always create a PR branch from `origin/main`. This prevents GitHub compare errors such as "No common ancestor".

```powershell
& 'C:\Program Files\Git\cmd\git.exe' fetch origin main
& 'C:\Program Files\Git\cmd\git.exe' switch -c codex/<short-task-name> origin/main
```

If already on a feature branch, verify it is based on `origin/main` before pushing:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' merge-base --is-ancestor origin/main HEAD
& 'C:\Program Files\Git\cmd\git.exe' status --short --branch
```

### Commit Only The Intended Scope

Inspect the working tree and stage only files that belong to the current small PR.

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status --short --branch
& 'C:\Program Files\Git\cmd\git.exe' diff -- <changed-files>
& 'C:\Program Files\Git\cmd\git.exe' add <changed-files>
& 'C:\Program Files\Git\cmd\git.exe' commit -m '<type>: <short description>'
```

Do not use `git add -A` when unrelated local changes exist.

### Push The Branch

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push -u origin codex/<short-task-name>
```

### Create The Draft PR

Prepare a Markdown body with the required PR sections. Prefer the GitHub plugin connector when it is visible in the current Codex tool list. If the connector is not available but `gh` is installed and authenticated, create the draft PR with GitHub CLI:

```powershell
gh pr create `
  --repo jyqin0203/AnytimeSpeak `
  --base main `
  --head codex/<short-task-name> `
  --draft `
  --title '<type>: <short description>' `
  --body-file <path-to-pr-body.md>
```

If neither the GitHub plugin connector nor `gh` is available, push the branch and report the compare URL so the repository owner can create the PR manually:

```text
https://github.com/jyqin0203/AnytimeSpeak/pull/new/codex/<short-task-name>
```

Every PR body must include:

- Title
- Feature description
- Implementation approach
- Test method
- Third-party libraries, APIs, or AI-generated code used

### Verify After Creating The PR

```powershell
gh pr view --repo jyqin0203/AnytimeSpeak --web
& 'C:\Program Files\Git\cmd\git.exe' status --short --branch
```

Also verify:

- The PR is a draft unless the user requested ready for review.
- The base branch is `main`.
- The head branch is `codex/<short-task-name>`.
- The changed files match the requested scope.
- No `.env`, API key, token, private credential, or unauthorized asset is included.

### Known Pitfalls

- Older notes in this repo assumed another computer where `C:\Program Files\GitHub CLI\gh.exe` existed. On this machine, that path does not exist.
- Git is available at `C:\Program Files\Git\cmd\git.exe`; use that absolute path for reliable local git operations.
- The GitHub plugin may be installed and enabled but still unavailable to an already-running Codex session. Start a new session if the GitHub connector tool does not appear.
- If using `gh`, it must be installed, reachable from `PATH` or an explicit absolute path, and authenticated before PR creation.
- Branches created from a local empty commit instead of `origin/main` can fail PR comparison.
- If the current working tree has unrelated local changes, use a separate `git worktree` from `origin/main` for the PR branch instead of stashing or overwriting user work.

## PR 1: Project Guidelines and Planning Documents

- Add `AGENTS.md`.
- Add project, PR, and product planning documents.
- Add README placeholders.
- Add `.gitignore`.

## PR 2: Project Initialization

- Initialize frontend and backend folders.
- Add basic package metadata and development commands.
- Add minimal health checks or placeholder scripts.
- Keep the app runnable without business features.

## PR 3: Frontend Foundation

- Add React + Vite + TypeScript setup.
- Add base layout, routing, and shared UI structure.
- Add a simple development page shell.

## PR 4: Scenario Selection

- Add scenario list for interview, restaurant ordering, and meeting.
- Add scenario metadata and selection state.
- Navigate from scenario selection to the practice page.

## PR 5: Practice Page

- Add conversation layout.
- Add user text input and message history.
- Add end-practice action.
- Use mock AI replies only.

## PR 6: Backend Basic API

- Add FastAPI app structure.
- Add health endpoint.
- Add mock chat endpoint.
- Add environment configuration pattern.

## PR 7: Frontend and Backend Integration

- Connect frontend practice page to backend chat endpoint.
- Add loading and error states.
- Keep mock mode available.

## PR 8: Speech Input

- Add browser `SpeechRecognition` support where available.
- Keep text input as fallback.
- Add clear unsupported-browser behavior.

## PR 9: Speech Playback

- Add browser `SpeechSynthesis` playback for AI replies.
- Add play, stop, and auto-play options.
- Keep text display as fallback.

## PR 10: Grammar and Expression Feedback

- Add feedback generation after user turns or at controlled checkpoints.
- Show grammar corrections and expression suggestions without over-interrupting practice.
- Support mock feedback for demos without API keys.

## PR 11: Post-Session Summary

- Add end-session summary flow.
- Summarize strengths, issues, useful expressions, and next practice suggestions.
- Store session summary locally for MVP.

## PR 12: Scoring System

- Add grammar, expression, fluency, scenario completion, and overall scores.
- Define score calculation rules.
- Show score history or simple progress indicators.

## PR 13: User Auth and Practice History

Current status: merged into `main`.

- Add SQLite database with users, practice_sessions, messages, and feedbacks tables.
- Add minimal username/password registration and login with salted password hashes; no OAuth.
- Add `POST /api/users/register`, `POST /api/users/login`, and `GET /api/users/{user_id}`.
- Add `POST /api/history/sessions`, `GET /api/history/sessions`, and `GET /api/history/sessions/{session_id}`.
- Auto-save practice history after each session ends; keep the completed session as a pending save if the backend is unavailable.
- Frontend history list and session detail views.
- Login/profile chip and History button in the topbar.
- Score panel shows an empty placeholder before the first turn instead of a hardcoded score.

## PR 14: README, Screenshots, and Demo Video Script

Current status: still needed for final submission materials. Do not add a demo video link until a real accessible link exists.

- Update README with final setup and demo steps.
- Add screenshot references.
- Add demo video script and recording checklist.
- Document third-party dependencies, APIs, and AI-generated code usage.

## Recommended Follow-Up PRs

- `fix: improve practice layout and demo usability`
- `feat: add streaming ASR provider`
- `docs: finalize submission materials`
