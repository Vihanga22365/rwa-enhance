#!/usr/bin/env bash
# Manual deploy / update, run on the server from this directory. The normal
# path is a push to master, which GitHub Actions builds and deploys; this is the
# fallback for when you need to build on the box itself.
#
#   ./deploy.sh            # pull latest code, rebuild, restart
#   ./deploy.sh --no-pull  # rebuild from current working tree (skip git pull)
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Run:  cp .env.example .env  and fill in your keys." >&2
  exit 1
fi

if [[ "${1:-}" != "--no-pull" ]] && git rev-parse --git-dir >/dev/null 2>&1; then
  echo ">> Pulling latest code..."
  git pull --ff-only
fi

# The images pinned by CI would otherwise win over the local build below.
if grep -qE '^(BACKEND|FRONTEND)_IMAGE=' .env; then
  echo ">> Clearing the CI-pinned image tags so this builds from source..."
  sed -i '/^BACKEND_IMAGE=/d;/^FRONTEND_IMAGE=/d' .env
fi

echo ">> Building and (re)starting containers..."
docker compose up -d --build

echo ">> Installing / reloading the /rwa-enhance route on the edge nginx..."
bash deploy/add-route-to-rwa-web.sh

echo ">> Pruning dangling images..."
docker image prune -f >/dev/null 2>&1 || true

echo ">> Current status:"
docker compose ps

echo ">> Done. Tail logs with:  docker compose logs -f"
