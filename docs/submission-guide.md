# Submission Guide

Use this guide before the final course submission. It focuses on the repository, demo video, README links, dependency disclosure, originality notes, and security checks.

## Final Submission Materials

- [ ] Public GitHub or Gitee repository link.
- [ ] Demo video link.
- [ ] README with setup, current status, demo instructions, and dependency notes.
- [ ] MVP checklist reviewed before submission.
- [ ] Demo script reviewed before recording.
- [ ] API contract available for explaining implemented frontend/backend integration.
- [ ] PR history shows small, focused changes across the development period.
- [ ] Commit history uses concise conventional commit messages.

## GitHub Repository Check

- [ ] Repository is public or accessible according to course rules.
- [ ] `main` branch is runnable after the latest merge.
- [ ] Latest README matches the actual implementation state.
- [ ] `docs/` contains project plan, product design, PR plan, demo script, MVP checklist, API contract, and submission guide.
- [ ] Pull requests are focused and include description, implementation approach, test method, and dependency/API disclosure.
- [ ] No unrelated generated files, local caches, build output, or editor settings are included.
- [ ] Commit timestamps and PR history satisfy course process requirements.

## Demo Video Upload And Link Check

- [ ] Video length is close to the required 3 to 5 minute range.
- [ ] Video shows the app starting from a clean local demo path.
- [ ] Video covers scenario selection, practice conversation, grammar/expression feedback, pronunciation assessment if voice is used, post-session summary, scores, history, and technical architecture.
- [ ] Video does not claim unimplemented features are complete.
- [ ] Video uses mock mode if API keys are unavailable.
- [ ] Video does not show `.env`, API keys, tokens, private accounts, or sensitive personal data.
- [ ] Video is uploaded to an accessible platform.
- [ ] README demo section contains the final video link.
- [ ] The final submission form or course platform also contains the same video link.

## README Check

- [ ] Project description is clear and matches AnytimeSpeak's MVP scope.
- [ ] Current status is accurate.
- [ ] Frontend setup command is documented.
- [ ] Backend setup command is documented.
- [ ] Health check command is documented.
- [ ] Mock mode or no-key demo behavior is documented when implemented.
- [ ] Demo video link is added before final submission.
- [ ] Third-party libraries, frameworks, APIs, and AI-generated code usage are disclosed.
- [ ] Security note reminds contributors not to commit credentials.

## Third-Party Dependencies And Originality

- [ ] README lists frontend dependencies such as React, Vite, and TypeScript.
- [ ] README lists backend dependencies such as FastAPI, Uvicorn, Pytest, and HTTPX.
- [ ] README states whether any AI API is integrated.
- [ ] PR descriptions disclose new third-party libraries or APIs whenever they are added.
- [ ] AI-generated code or AI-assisted documentation is disclosed according to course requirements.
- [ ] Mock data is original, fictional, and free of personal information.
- [ ] No unauthorized media, copied assets, or infringing material is included.

## Security Check

- [ ] `.env` and `.env.*` files are ignored except `.env.example`.
- [ ] No API keys, tokens, private credentials, or provider secrets are committed.
- [ ] Demo screenshots and videos do not expose secrets.
- [ ] Provider configuration uses environment variables.
- [ ] Mock mode works without private credentials.
- [ ] Sample messages do not include real personal data.

## Final PR Checklist

- [ ] PR title follows the required format.
- [ ] PR description includes feature description.
- [ ] PR description includes implementation approach.
- [ ] PR description includes test method.
- [ ] PR description includes third-party libraries, APIs, or AI-generated code used.
- [ ] Commit message follows project conventions.
- [ ] The PR is docs-only when the task scope is docs-only.
- [ ] The diff does not modify `frontend/` or `backend/` unless the PR explicitly requires it.

## Suggested Final Submission Order

1. Merge final MVP code PRs after tests pass.
2. Run the MVP checklist.
3. Record the demo video using the demo script.
4. Upload the video and verify the public link.
5. Update README with the final video link and current status.
6. Re-check dependency, originality, and security notes.
7. Submit the repository link and demo video link.
