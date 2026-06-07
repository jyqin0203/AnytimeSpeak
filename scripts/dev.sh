#!/usr/bin/env sh
set -e

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

echo "========================================"
echo "AnytimeSpeak local development"
echo "========================================"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://127.0.0.1:8000"
echo
echo "Frontend uses Vite dev server with HMR."
echo "Backend uses Uvicorn with --reload."
echo "Press Ctrl+C to stop both services."
echo

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup INT TERM EXIT

(cd "$ROOT_DIR/backend" && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
BACKEND_PID=$!

(cd "$ROOT_DIR/frontend" && npm run dev -- --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
