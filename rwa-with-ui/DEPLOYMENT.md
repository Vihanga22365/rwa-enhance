# Production Deployment — Contabo VPS (91.230.110.121)

Live at **http://91.230.110.121/rwa-enhance/**

Deploys are automatic: push to `master`, GitHub Actions builds both images, pushes
them to GHCR, and restarts the stack over SSH. Nothing is built on the VPS.

```
push to master
   │
   ├─ build  (GitHub runner)  Backend image ──┐
   │                          Frontend image ─┤─► ghcr.io/vihanga22365/rwa-enhance-*
   │                                          │
   └─ deploy (ssh to VPS) ─── git reset ──────┴─► docker compose pull && up -d
                              └─ add-route-to-rwa-web.sh (nginx reload)
```

---

## 1. How this host is laid out

The VPS runs five stacks side by side. **Ports 80 and 443 are already taken**, so
this app publishes no host port at all. Instead, the `rwa-web-1` nginx owns port
80 and routes every app by path prefix over the external `shared-edge` Docker
network:

| Path                   | Upstream (alias on `shared-edge`) | Stack                       |
| ---------------------- | --------------------------------- | --------------------------- |
| `/`                    | served by `rwa-web-1` itself       | `~/rwa` (the original RWA)  |
| `/mrm/`                | `mrm-frontend`                     | `/opt/mrm`                  |
| `/presentation-agent/` | `presentation-agent-frontend`      | `/opt/presentation-agent`   |
| `/qa-task-automation/` | `qa-task-automation-frontend`      | `/opt/qa-task-automation`   |
| `/rwa-enhance/`        | `rwa-enhance-frontend`             | `/opt/rwa-enhance` ← **this** |

HTTPS on `:443` is terminated by `presentation-agent-tls-proxy-1`, which forwards
what it does not own to `rwa-web-1`. So this app is reachable over both schemes
without that proxy being touched.

To see what is actually bound at any time:

```bash
sudo ss -tulnp
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

### The two containers in this stack

| Container             | Image                                      | Published | Reached via                          |
| --------------------- | ------------------------------------------ | --------- | ------------------------------------ |
| `rwa-enhance-web`     | `ghcr.io/…/rwa-enhance-frontend:<sha>`     | nothing   | `shared-edge` alias `rwa-enhance-frontend` |
| `rwa-enhance-backend` | `ghcr.io/…/rwa-enhance-backend:<sha>`      | nothing   | internal network only                |

The backend is never exposed to the host, let alone the internet: the only way
in is `rwa-enhance-web`'s nginx, which proxies `/rwa-enhance/api/*` to it.

### The sub-path is fixed in four places

`/rwa-enhance/` has to agree across:

1. `Frontend/Dockerfile` — `ARG APP_BASE_PATH`, compiled into `<base href>`
2. `Frontend/Dockerfile` — the directory the bundle is copied into
3. `Frontend/nginx.conf` — every `location` block
4. `deploy/rwa-web-route.conf` — the route installed into `rwa-web-1`

The frontend code itself does **not** hard-code it: `rwa-agent-api.service.ts`
resolves the API base against `document.baseURI`, so the compiled `<base href>`
is the single source of truth at runtime.

---

## 2. First-time server setup

Only needed once; it has already been done for this app.

```bash
ssh deploy@91.230.110.121

sudo mkdir -p /opt/rwa-enhance
sudo chown deploy:deploy /opt/rwa-enhance
git clone https://github.com/Vihanga22365/rwa-enhance.git /opt/rwa-enhance

cd /opt/rwa-enhance/rwa-with-ui
cp .env.example .env
nano .env            # set OPENAI_API_KEY at minimum
```

`shared-edge` already exists (the original `rwa` stack created it). Confirm
rather than recreate — a second, empty network would silently break routing:

```bash
docker network inspect shared-edge >/dev/null && echo present
```

---

## 3. GitHub Actions secrets

Repository → **Settings → Secrets and variables → Actions → Repository secrets**
(not Variables, not an Environment):

| Secret           | Value                                              |
| ---------------- | -------------------------------------------------- |
| `DEPLOY_HOST`    | `91.230.110.121`                                   |
| `DEPLOY_USER`    | `deploy`                                           |
| `DEPLOY_SSH_KEY` | the **private** key, `BEGIN`/`END` lines included  |
| `DEPLOY_PORT`    | `22` (optional — 22 is assumed)                    |

`GITHUB_TOKEN` is provided automatically and is what pushes to GHCR and lets the
server pull from it.

To mint a fresh key pair for CI:

```bash
ssh-keygen -t ed25519 -C rwa-enhance-ci -f ./rwa-enhance-ci -N ''
# public half onto the server:
ssh deploy@91.230.110.121 'cat >> ~/.ssh/authorized_keys' < rwa-enhance-ci.pub
# private half into DEPLOY_SSH_KEY, then delete your local copy
```

---

## 4. Day-2 operations

All from `/opt/rwa-enhance/rwa-with-ui`.

```bash
docker compose ps                       # what is running
docker compose logs -f backend          # agent traces, LLM errors
docker compose logs -f web              # nginx access/error
docker compose restart backend          # after an .env change
docker compose down                     # stop this app (others unaffected)
```

Roll back to a previous release without a new build — every deploy pins the
exact tags in `.env`:

```bash
sed -i 's#^BACKEND_IMAGE=.*#BACKEND_IMAGE=ghcr.io/vihanga22365/rwa-enhance-backend:<sha>#' .env
sed -i 's#^FRONTEND_IMAGE=.*#FRONTEND_IMAGE=ghcr.io/vihanga22365/rwa-enhance-frontend:<sha>#' .env
docker compose up -d
```

Build on the box instead of via CI (fallback only — competes for memory with the
other four stacks):

```bash
./deploy.sh
```

### The nginx route

`deploy/add-route-to-rwa-web.sh` installs the `/rwa-enhance/` block into
`rwa-web-1`'s config and reloads it. It is idempotent and runs on every deploy.
A reload is not a restart — in-flight requests to the other apps finish
normally, and nothing on the box goes down.

```bash
bash deploy/add-route-to-rwa-web.sh --check   # show the diff, change nothing
bash deploy/add-route-to-rwa-web.sh           # install / reload
```

**This route lives inside the `rwa-web-1` container, not in a file on the host.**
Redeploying the *original* `rwa` stack (`~/rwa`) replaces that container and
wipes the routes for `/mrm/`, `/presentation-agent/`, `/qa-task-automation/`
**and** `/rwa-enhance/`. Each app reinstalls its own on the next deploy; for this
one, re-run the script above.

Rollback, if a config edit ever goes wrong:

```bash
docker exec rwa-web-1 sh -c 'ls /etc/nginx/conf.d/app.conf.bak.*'
docker exec rwa-web-1 sh -c 'cp /etc/nginx/conf.d/app.conf.bak.<STAMP> /etc/nginx/conf.d/app.conf'
docker exec rwa-web-1 nginx -t && docker exec rwa-web-1 nginx -s reload
```

---

## 5. Verifying a deploy

The stack publishes no port, so "is it up?" is answered through the router that
actually serves it:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost/rwa-enhance/
curl -s http://localhost/rwa-enhance/health              # {"status":"ok"}
curl -s http://localhost/rwa-enhance/api/rwa/config      # models + issue types
```

A status code alone proves nothing for the app path: the original RWA app's
`location /` catch-all answers **200 with its own index.html** for anything
unrouted, so a missing route looks identical to a working one. Check the title:

```bash
curl -sL http://localhost/rwa-enhance/ | grep -o '<title>[^<]*</title>'
```

And confirm the neighbours still work — a deploy here must never be what breaks
them:

```bash
for p in / /mrm/ /presentation-agent/ /qa-task-automation/ /rwa-enhance/; do
  printf '%-24s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' http://localhost$p)"
done
```

---

## 6. Scaling & limitations

- **Sessions are in-process.** `app/api/sessions.py` is a plain dict, so the
  backend runs a single uvicorn worker on purpose. Adding workers or replicas
  splits sessions across processes and follow-up questions start losing their
  context. A shared store (Redis) is the prerequisite for scaling out.
- **Long requests.** One `/email-submit` walks a whole decision tree — dozens of
  sequential LLM calls, minutes of wall clock. Timeouts are set generously at
  both nginx hops (900s in this app's nginx, 3600s at the edge) so the backend is
  always the component that decides a request has taken too long.
- **Shared box.** 11 GB RAM across five stacks. That is why CI builds the images
  and the VPS only pulls them.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `/rwa-enhance/` shows the *original* RWA app | route not installed in `rwa-web-1` | `bash deploy/add-route-to-rwa-web.sh` |
| `502` on `/rwa-enhance/` | `rwa-enhance-web` down, or not on `shared-edge` | `docker compose ps`; `docker network inspect shared-edge` |
| `502` only on `/rwa-enhance/api/…` | backend unhealthy | `docker compose logs backend` |
| Blank page, 404s for `main-*.js` | bundle built with the wrong `--base-href` | check `APP_BASE_PATH` reached the build; `docker exec rwa-enhance-web grep '<base' /usr/share/nginx/html/rwa-enhance/index.html` |
| API calls go to `/api/rwa/…` (no prefix) | stale bundle from before the sub-path change | hard-reload; `index.html` is served `no-store`, assets are hashed |
| Deploy fails at "Check the deploy secrets are set" | missing Actions secret | see §3 |
| `shared-edge network missing — aborting` | the original `rwa` stack was removed | that breaks `/mrm/` and the others too; bring `~/rwa` back up first |
