@echo off
setlocal

echo ========================================
echo Stopping AnytimeSpeak local development
echo ========================================

call :stop_port 5173 "Frontend"
call :stop_port 8000 "Backend"

echo.
echo Stop command completed.
exit /b 0

:stop_port
set "PORT=%~1"
set "LABEL=%~2"
set "FOUND="

echo.
echo Checking %LABEL% on port %PORT%...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "FOUND=1"
  echo Stopping PID %%P for %LABEL%...
  taskkill /PID %%P /T /F >nul 2>nul
  if errorlevel 1 (
    echo Failed to stop PID %%P. It may already be stopped or require administrator permission.
  ) else (
    echo Stopped PID %%P.
  )
)

if not defined FOUND (
  echo No running %LABEL% process found on port %PORT%.
)

exit /b 0
