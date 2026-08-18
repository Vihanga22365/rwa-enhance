#!/usr/bin/env bash
# Add the /rwa-enhance route to the rwa-web-1 nginx, which owns port 80 and
# path-routes for the whole server.
#
#   ./deploy/add-route-to-rwa-web.sh          # install (idempotent)
#   ./deploy/add-route-to-rwa-web.sh --check  # show what would change, do nothing
#
# This is a config reload, NOT a container restart: `nginx -s reload` starts new
# worker processes and lets the old ones finish their in-flight requests. The
# original RWA app, /mrm/, /presentation-agent/ and /qa-task-automation/ keep
# serving throughout — no dropped connections, no downtime for anything else on
# this box.
#
# Everything is validated with `nginx -t` before the reload, and the previous
# config is backed up inside the container first, so a mistake is one `docker cp`
# away from being undone (see ROLLBACK at the bottom).
#
# Safe to re-run on every deploy: when the route is already there it only
# reloads, which re-resolves the upstream container's address.
set -euo pipefail

ROUTER=rwa-web-1
CONF=/etc/nginx/conf.d/app.conf
MARKER=rwa-enhance-frontend

cd "$(dirname "$0")/.."
SNIPPET="$PWD/deploy/rwa-web-route.conf"
[[ -f $SNIPPET ]] || { echo "ERROR: $SNIPPET not found" >&2; exit 1; }

if ! docker ps --format '{{.Names}}' | grep -qx "$ROUTER"; then
  echo "ERROR: container '$ROUTER' is not running. It owns port 80 and is the" >&2
  echo "       path router — nothing can be added until it is up." >&2
  exit 1
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

docker cp "$ROUTER:$CONF" "$WORK/app.conf" >/dev/null

if grep -q "$MARKER" "$WORK/app.conf"; then
  echo ">> Route already present in $ROUTER:$CONF — nothing to do."
  echo ">> Reloading anyway so the upstream is re-resolved."
  docker exec "$ROUTER" nginx -t
  docker exec "$ROUTER" nginx -s reload
  exit 0
fi

# Insert before the catch-all `location / {`, so the new prefix is matched
# before the original RWA SPA fallback claims it. Exit 3 if that anchor is
# missing, rather than writing a config that silently does the wrong thing.
awk -v snippet="$SNIPPET" '
  !inserted && /^[[:space:]]*location \/ \{/ {
    while ((getline line < snippet) > 0) print line
    print ""
    inserted = 1
  }
  { print }
  END { if (!inserted) exit 3 }
' "$WORK/app.conf" > "$WORK/app.conf.new" || {
  echo "ERROR: could not find the 'location / {' anchor in $CONF." >&2
  echo "       Add the contents of $SNIPPET by hand instead." >&2
  exit 3
}

if [[ "${1:-}" == "--check" ]]; then
  echo ">> Would apply this change to $ROUTER:$CONF:"
  diff -u "$WORK/app.conf" "$WORK/app.conf.new" || true
  exit 0
fi

STAMP=$(date +%s)
echo ">> Backing up to $ROUTER:$CONF.bak.$STAMP"
docker exec "$ROUTER" cp "$CONF" "$CONF.bak.$STAMP"

echo ">> Installing the route..."
docker cp "$WORK/app.conf.new" "$ROUTER:$CONF" >/dev/null

echo ">> Validating..."
if ! docker exec "$ROUTER" nginx -t; then
  echo "!! Config invalid — restoring the backup and leaving nginx untouched." >&2
  docker exec "$ROUTER" cp "$CONF.bak.$STAMP" "$CONF"
  exit 1
fi

echo ">> Reloading nginx (no restart, no dropped connections)..."
docker exec "$ROUTER" nginx -s reload

echo ">> Done. Verifying every path on the router:"
# The status code alone proves nothing for the new path: the original RWA app's
# `location /` catch-all answers 200 with its OWN index.html for anything
# unrouted, so an uninstalled route looks identical to a working one. The page
# title is what actually distinguishes them.
for path in / /mrm/ /presentation-agent/ /qa-task-automation/ /rwa-enhance/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost$path")
  # `|| true` is load-bearing: a redirect has no <title>, grep exits 1 on no
  # match, and under `set -euo pipefail` that would abort the script here —
  # after the route is already installed, making a success look like a failure.
  title=$(curl -sL "http://localhost$path" | grep -o '<title>[^<]*</title>' | head -1 || true)
  printf '   %-24s %-4s %s\n' "$path" "$code" "${title:-<no title>}"
done

# ROLLBACK
#   docker exec rwa-web-1 sh -c 'cp /etc/nginx/conf.d/app.conf.bak.<STAMP> /etc/nginx/conf.d/app.conf'
#   docker exec rwa-web-1 nginx -t && docker exec rwa-web-1 nginx -s reload
