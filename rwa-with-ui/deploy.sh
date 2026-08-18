#!/usr/bin/env bash
# Idempotent deploy / update script. Run on the server from the repo root.
#   ./deploy.sh            # pull latest code, rebuild, restart
#   ./deploy.sh --no-pull  # rebuild from current working tree (skip git pull)
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Run:  cp .env.example .env  and fill in your keys." >&2
  exit 1
fi

if [[ "${1:-}" != "--no-pull" ]] && [[ -d .git ]]; then
  echo ">> Pulling latest code..."
  git pull --ff-only
fi

echo ">> Building and (re)starting containers..."
docker compose up -d --build

echo ">> Pruning dangling images..."
docker image prune -f >/dev/null 2>&1 || true

echo ">> Current status:"
docker compose ps

echo ">> Done. Tail logs with:  docker compose logs -f"
