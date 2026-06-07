#!/usr/bin/env sh
set -e

echo "========================================"
echo "Stopping AnytimeSpeak local development"
echo "========================================"

stop_port() {
  port="$1"
  label="$2"

  echo
  echo "Checking $label on port $port..."

  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [ -z "$pids" ]; then
    echo "No running $label process found on port $port."
    return
  fi

  echo "$pids" | while IFS= read -r pid; do
    if [ -n "$pid" ]; then
      echo "Stopping PID $pid for $label..."
      kill "$pid" 2>/dev/null || true
    fi
  done
}

stop_port 5173 "Frontend"
stop_port 8000 "Backend"

echo
echo "Stop command completed."
