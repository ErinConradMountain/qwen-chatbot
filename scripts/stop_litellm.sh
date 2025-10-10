#!/usr/bin/env bash
set -euo pipefail
PID_FILE=".run/litellm.pid"
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" || true
    echo "Stopped LiteLLM (pid $PID)"
  fi
  rm -f "$PID_FILE"
else
  echo "No PID file found at $PID_FILE"
fi

