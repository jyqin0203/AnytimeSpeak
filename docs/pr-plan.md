# PR Plan

This project should be developed through small, focused PRs. Each PR should keep `main` runnable and include a clear description, implementation approach, test method, and dependency/API disclosure.

## Current Status Source Of Truth

The early PR numbering below is planning history, not a guaranteed statement of what is currently missing. When early PR numbers or old notes conflict with the current implementation, use these sources in this order:

1. Current code on `main`.
2. README current status and feature list.
3. `docs/api-contract.md` current implemented sections.

Do not re-implement a feature just because an old numbered PR title mentions it.

## Agent PR Workflow

Always start from remote main:

```powershell
git fetch origin main
git switch -c codex/<short-task-name> origin/main
```

Inspect and stage only intended files:

```powershell
git status --short --branch
git diff -- <changed-files>
git add <changed-files>
git commit -m "<type>: <short description>"
```

Push:

```powershell
git push -u origin codex/<short-task-name>
```

Every PR body must include:

- Title.
- Feature description.
- Implementation approach.
- Test method.
- Third-party libraries, APIs, or AI-generated code used.

Do not use `git add -A` when unrelated local files exist. Never stage `.env`, API keys, tokens, runtime database files, `node_modules`, build output, or caches.

## Completed PR History

- PR 1: Project guidelines and planning documents.
- PR 2: Project initialization.
- PR 3: Frontend foundation.
- PR 4: Scenario selection.
- PR 5: Practice page.
- PR 6: Backend basic API.
- PR 7: Frontend/backend integration.
- PR 8: Browser speech input.
- PR 9: Speech playback.
- PR 10: Grammar and expression feedback.
- PR 11: Post-session summary.
- PR 12: Scoring system.
- PR 13: User auth and SQLite practice history.
- PR 14: Practice UI/UX improvements.
- PR 16: Doubao Streaming ASR provider.
- PR 18: Pronunciation assessment fallback and optional XFYUN provider.

## Current PR

Title:

```text
docs: finalize repository documentation and submission readiness
```

Scope:

- Final repository scan.
- Chinese-first README.
- Screenshots under `docs/assets/`.
- Cleanup of obsolete temporary docs.
- API/product/demo/checklist updates aligned with current `main`.
- Build/test/security verification.

This PR should remain docs-focused and must not modify core frontend/backend logic.

## Recommended Follow-Up PRs

- `docs: add final demo video link` after the video is uploaded and accessible.
- `fix: polish optional ASR reliability` if Doubao provider testing finds browser/network edge cases.
- `fix: polish optional pronunciation provider output` if XFYUN test credentials reveal score mapping issues.
- `fix: polish LLM output formatting` if real provider responses need additional sanitization.
