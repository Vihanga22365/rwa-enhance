#!/usr/bin/env bash
# Create the virtualenv and install dependencies.
#   ./scripts/setup.sh
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON_BIN="$candidate"; break; fi
  done
fi
if [ -z "$PYTHON_BIN" ]; then
  echo "No suitable Python found. Install Python 3.11+ and retry." >&2
  exit 1
fi

echo "Using $($PYTHON_BIN --version) at $(command -v "$PYTHON_BIN")"

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
  echo "Created .venv"
fi

./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "Created Backend/.env -- add your OPENAI_API_KEY to it."
fi

echo
echo "Done. Next:"
echo "  1. Put your key in Backend/.env       (OPENAI_API_KEY=sk-...)"
echo "  2. ./.venv/bin/python -m app.llm.check   (verify model + thinking level)"
echo "  3. ./scripts/run_api.sh                  (start the API on :8000)"
