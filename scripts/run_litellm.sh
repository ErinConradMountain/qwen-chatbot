#!/usr/bin/env bash
set -euo pipefail
CONFIG=${1:-litellm_config.yaml}
PORT=${PORT:-4000}
RUN_DIR=".run"
PID_FILE="$RUN_DIR/litellm.pid"

python - <<'PY'
import importlib, sys
sys.exit(0 if importlib.util.find_spec('litellm') else 1)
PY
if [ $? -ne 0 ]; then
  pip install -r requirements-dev.txt || pip install 'litellm[proxy]' 
fi

mkdir -p "$RUN_DIR"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  echo "LiteLLM already running with PID $(cat "$PID_FILE")"
  exit 0
fi

export LITELLM_CONFIG=$(realpath "$CONFIG")
nohup python -m litellm --host 127.0.0.1 --port=$PORT --config "$LITELLM_CONFIG" >/dev/null 2>&1 &
echo $! > "$PID_FILE"
echo "LiteLLM proxy started on http://127.0.0.1:$PORT using $CONFIG (pid $(cat "$PID_FILE"))"
