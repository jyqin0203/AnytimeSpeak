# PR Plan

This project should be developed through small, focused PRs. Each PR should keep `main` runnable and include a clear description, implementation approach, test method, and dependency/API disclosure.

## Agent PR Submission Guide

This section is the canonical PR workflow for Codex/Coding Agents working on this repository. Follow it before opening any future PR.

### Required Tools

Use local Git plus GitHub CLI. On this Windows machine, the tools may not be available through `PATH`, so use absolute paths first:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' --version
& 'C:\Program Files\GitHub CLI\gh.exe' --version
& 'C:\Program Files\GitHub CLI\gh.exe' auth status
```

If GitHub CLI is not logged in, ask the repository owner to run:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' auth login
```

If `gh` reports that it cannot find `git`, fix the current shell session with:

```powershell
$env:Path = 'C:\Program Files\Git\cmd;' + $env:Path
```

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

Prepare a Markdown body file that includes the required PR sections, then create the draft PR:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' pr create `
  --repo jyqin0203/AnytimeSpeak `
  --base main `
  --head codex/<short-task-name> `
  --draft `
  --title '<type>: <short description>' `
  --body-file <path-to-pr-body.md>
```

Every PR body must include:

- Title
- Feature description
- Implementation approach
- Test method
- Third-party libraries, APIs, or AI-generated code used

### Verify After Creating The PR

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' pr view --repo jyqin0203/AnytimeSpeak --web
& 'C:\Program Files\Git\cmd\git.exe' status --short --branch
```

Also verify:

- The PR is a draft unless the user requested ready for review.
- The base branch is `main`.
- The head branch is `codex/<short-task-name>`.
- The changed files match the requested scope.
- No `.env`, API key, token, private credential, or unauthorized asset is included.

### Known Pitfalls

- GitHub connector write actions may return `403 Resource not accessible by integration`; use local Git and `gh` instead.
- `git` may be installed but missing from `PATH`; use `C:\Program Files\Git\cmd\git.exe`.
- `gh` may be installed but missing from `PATH`; use `C:\Program Files\GitHub CLI\gh.exe`.
- `gh pr create` may fail if `gh auth status` is not logged in.
- Branches created from a local empty commit instead of `origin/main` can fail PR comparison.

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

- Add SQLite database with users, practice_sessions, messages, and feedbacks tables.
- Add minimal username/password registration and login with salted password hashes; no OAuth.
- Add `POST /api/users/register`, `POST /api/users/login`, and `GET /api/users/{user_id}`.
- Add `POST /api/history/sessions`, `GET /api/history/sessions`, and `GET /api/history/sessions/{session_id}`.
- Auto-save practice history after each session ends; keep the completed session as a pending save if the backend is unavailable.
- Frontend history list and session detail views.
- Login/profile chip and History button in the topbar.
- Score panel shows an empty placeholder before the first turn instead of a hardcoded score.
## PR 14: README, Screenshots, and Demo Video Script

- Update README with final setup and demo steps.
- Add screenshot references.
- Add demo video script and recording checklist.
- Document third-party dependencies, APIs, and AI-generated code usage.

