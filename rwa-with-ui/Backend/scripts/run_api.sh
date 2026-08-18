#!/usr/bin/env bash
# Start the FastAPI backend on :8000 with auto-reload.
#   ./scripts/run_api.sh
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

if [ ! -x .venv/bin/uvicorn ]; then
  echo "No .venv found. Run ./scripts/setup.sh first." >&2
  exit 1
fi

exec ./.venv/bin/uvicorn app.main:app \
  --host "${API_HOST:-0.0.0.0}" \
  --port "${API_PORT:-8000}" \
  --workers 1 \
  --reload
