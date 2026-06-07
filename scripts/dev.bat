@echo off
setlocal

set "ROOT_DIR=%~dp0.."
set "BACKEND_DIR=%ROOT_DIR%\backend"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"

echo ========================================
echo AnytimeSpeak local development
echo ========================================
echo Frontend: http://localhost:5173
echo Backend:  http://127.0.0.1:8000
echo.
echo Frontend uses Vite dev server with HMR.
echo Backend uses Uvicorn with --reload.
echo Close both terminal windows to stop the services.
echo.

start "AnytimeSpeak Backend" /D "%BACKEND_DIR%" cmd /k uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
start "AnytimeSpeak Frontend" /D "%FRONTEND_DIR%" cmd /k npm run dev -- --host 127.0.0.1 --port 5173

echo Started frontend and backend in separate terminal windows.
