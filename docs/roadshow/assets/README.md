# Roadshow screenshot assets

Screenshot session: local demo run on 2026-06-16.

Provider mode: backend started with `LLM_PROVIDER_MODE=mock`; screenshots use backend mock/fallback behavior. No real provider credentials were used or shown.

| File | Captured page / area | Suggested slide | Status / notes |
| --- | --- | --- | --- |
| `01-home.png` | Home / product entry page | Slide 3 product loop; Slide 11 product screenshot thumbnail | Available |
| `02-profile-login.png` | Login / register profile modal | Slide 4 core feature, profile and history support | Available |
| `03-scenario-selection.png` | Scenario selection page with multiple scenario cards | Slide 4 core features | Available |
| `04-daily-scenario-card.png` | Daily conversation scenario card / selected scenario card area | Slide 5 scenario design | Available |
| `05-practice-start.png` | Practice page initial state with story intro and AI opening | Slide 9 live demo | Available |
| `06-practice-chat.png` | Practice page after multiple conversation turns | Slide 7 session flow; Slide 9 live demo | Available |
| `07-feedback-panel.png` | Immediate feedback panel with recommendation, explanation, and score breakdown | Slide 4 core features | Available |
| `08-speech-input.png` | Text composer and microphone / speech input controls | Slide 4 core features; Slide 9 live demo | Available |
| `09-summary.png` | Post-session summary page with scores | Slide 4 core features | Available |
| `10-history-list.png` | Practice history list page | Slide 4 core features | Available |
| `11-history-detail.png` | Practice history detail page | Slide 4 core features | Available |
| `12-provider-status.png` | Provider / fallback status banner | Slide 8 provider + fallback | Available |

Missing screenshots: none.

Startup commands used:

```powershell
cd backend
$env:LLM_PROVIDER_MODE="mock"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Validation notes:

- Backend health check returned `{"status":"ok"}`.
- Frontend returned HTTP 200 at `http://127.0.0.1:5173`.
- Screenshots were captured with Playwright Chromium at 1600x1000 viewport and browser UI excluded.
- No `.env`, API key, token, provider console, terminal window, or database file is visible in the screenshots.
