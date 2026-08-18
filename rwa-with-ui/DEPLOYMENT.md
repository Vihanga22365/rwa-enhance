# Production Deployment — Contabo VPS (91.230.110.121)

This deploys the app as two Docker containers behind a single nginx entry point:

```
                   Internet
                      │  :80  (later :443)
            ┌─────────▼─────────┐
            │   web (nginx)     │   serves Angular SPA
            │   rwa-frontend    │   proxies /api ─┐
            └───────────────────┘                 │  internal docker network
            ┌───────────────────┐                 │
            │ backend (uvicorn) │ ◄───────────────┘  :8000 (not public)
            │   rwa-backend     │   FastAPI + LangGraph
            └───────────────────┘
```

Why this shape: one public port, backend + API keys never exposed, frontend and
API are same-origin (no CORS headaches, no mixed-content when you add HTTPS),
and the whole stack comes up / rolls back with one command.

---

## 0. Prerequisites (local, one-time)

Commit the new deployment files to your repo and push, so the server can pull:

```bash
git add Backend/Dockerfile Backend/.dockerignore \
        Frontend/Dockerfile Frontend/nginx.conf Frontend/.dockerignore \
        Frontend/src/environments/environment.prod.ts Frontend/angular.json \
        Backend/app/ Backend/config/ docker-compose.yml .env.example deploy.sh \
        DEPLOYMENT.md .gitignore
git commit -m "Add production Docker deployment"
git push
```

> If the repo isn't reachable from the server, you can instead copy the folder up
> with `scp -r` or `rsync` (see Appendix B).

---

## 1. First connection & a non-root user

SSH in as root (Contabo emails you the root password):

```bash
ssh root@91.230.110.121
```

Create a sudo user and use it from now on (don't run the app as root):

```bash
adduser deploy
usermod -aG sudo deploy
# copy your SSH key so you can log in as deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Reconnect: `ssh deploy@91.230.110.121`

Recommended hardening in `/etc/ssh/sshd_config` (then `sudo systemctl restart ssh`):

```
PermitRootLogin no
PasswordAuthentication no   # only after confirming key login works!
```

---

## 2. Install Docker Engine + Compose plugin

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# run docker without sudo (log out/in afterwards for it to take effect)
sudo usermod -aG docker $USER
```

Verify: `docker --version && docker compose version`

---

## 3. Firewall

```bash
sudo apt-get install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp     # for HTTPS later
sudo ufw enable
sudo ufw status
```

> Also check the **Contabo control panel firewall** — by default it's open, but if
> you've enabled it there, allow 22/80/443 too.

---

## 4. Get the code and set secrets

```bash
cd ~
git clone <YOUR_REPO_URL> rwa && cd rwa
# (or scp the folder up — see Appendix B)

cp .env.example .env
nano .env        # paste your real OPENAI_API_KEY (and others). Save.
```

`.env` must use `KEY=value` with **no spaces** around `=`. It is git-ignored.

---

## 5. Launch

```bash
chmod +x deploy.sh
./deploy.sh
```

This builds both images and starts the stack. First build takes a few minutes
(Angular build + Python deps). Then verify:

```bash
docker compose ps                  # both services should be "running" / "healthy"
curl -s http://localhost/health    # -> {"status":"ok"}  (nginx -> backend)
```

Open in a browser: **http://91.230.110.121**  (and `http://91.230.110.121/health`)

The UI calls `/api/rwa/...` on the same origin; nginx forwards it to the backend.

---

## 6. Day-2 operations

```bash
docker compose logs -f               # tail all logs
docker compose logs -f backend       # just the API
docker compose restart backend       # restart one service
docker compose down                  # stop everything
./deploy.sh                          # pull + rebuild + restart (normal update)
./deploy.sh --no-pull                # rebuild from local files without git pull
```

Containers have `restart: unless-stopped`, so they survive reboots and crashes.

---

## 6b. Automated deploys with GitHub Actions (recommended)

Manual `./deploy.sh` builds on the VPS (RAM-hungry). The included workflow
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) instead builds the
images on GitHub's runners, pushes them to **GHCR**, and the VPS only *pulls*:

```
push to master ─▶ build backend+frontend ─▶ ghcr.io/<owner>/<repo>-{backend,frontend}:<sha>
                                          └▶ SSH to VPS ─▶ docker compose pull && up -d
```

Each deploy pins the exact commit SHA (immutable releases + easy rollback).

### One-time setup

1. **Server prep (same as §1–§5)** — Docker installed, repo cloned at `~/rwa`,
   and `.env` filled with your real keys. You do *not* need to run `./deploy.sh`;
   Actions will start the stack on the first push.

2. **Create an SSH key pair for CI** (on your machine):
   ```bash
   ssh-keygen -t ed25519 -f deploy_key -C "github-actions" -N ""
   ssh-copy-id -i deploy_key.pub deploy@91.230.110.121   # add public key to server
   ```

3. **Add repository secrets** (GitHub → Settings → Secrets and variables → Actions):

   | Secret | Value |
   |---|---|
   | `DEPLOY_HOST` | `91.230.110.121` |
   | `DEPLOY_USER` | `deploy` |
   | `DEPLOY_PORT` | `22` |
   | `DEPLOY_SSH_KEY` | contents of the **private** `deploy_key` file |

   No registry secret is needed — the workflow uses the built-in `GITHUB_TOKEN`
   to push to GHCR and to log the server into GHCR during the run.

4. **First run**: push to `master` (or run the workflow manually via
   *Actions → Build & Deploy → Run workflow*). After the first push, confirm the
   two packages exist under your GitHub profile → *Packages*.

### Notes
- If the repo is **private**, its GHCR packages are private too. The in-run
  `GITHUB_TOKEN` can still pull them during deploy — nothing extra needed. If you
  ever pull manually on the server, `docker login ghcr.io` with a read PAT first.
- The deploy step writes `BACKEND_IMAGE`/`FRONTEND_IMAGE` into the server's `.env`
  so reboots and manual `docker compose` calls reuse the same release.
- **Rollback**: re-run the workflow for an older commit, or on the server set
  `BACKEND_IMAGE`/`FRONTEND_IMAGE` in `.env` to a previous `:<sha>` and
  `docker compose up -d`.

---

## 7. Add a domain + HTTPS (when ready)

The app is already same-origin and proxy-based, so going HTTPS is a small change.

1. Point an `A` record for your domain at `91.230.110.121`.
2. Add a TLS-terminating proxy. Easiest is **Caddy** (automatic Let's Encrypt):
   create `Caddyfile`:
   ```
   app.example.com {
       reverse_proxy web:80
   }
   ```
   and add a `caddy` service to `docker-compose.yml` publishing 80/443, then stop
   publishing 80 from `web`. Caddy fetches and renews certificates automatically.
   Alternatively use nginx + certbot, or Contabo's load balancer.
3. Update `.env`: `CORS_ORIGINS=https://app.example.com`, then `./deploy.sh`.

No frontend rebuild is needed for the API URL — it's relative (`/api`).

---

## 8. Scaling & limitations (read this)

- **Single backend worker on purpose.** `app/api/sessions.py` stores sessions in
  an in-process dict (`_store`). Running multiple uvicorn workers or backend
  replicas would split sessions across processes and break follow-up calls. To
  scale horizontally, move sessions to a shared store (e.g. Redis) and then raise
  `--workers` / add replicas + sticky sessions.
- **LLM calls are slow.** nginx and the stack are configured with 300s proxy
  timeouts to accommodate multi-agent runs. Tune in `Frontend/nginx.conf`.
- **Resources.** LangChain + pandas + the Angular build are memory-hungry to
  build. Use a Contabo plan with **≥4 GB RAM**; if builds get OOM-killed, build
  the frontend image locally and `docker save`/`load` it, or add swap.

---

## Appendix A — Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `502 Bad Gateway` on `/api` | backend still starting or crashed → `docker compose logs backend` |
| UI loads but API 500s | missing/invalid `OPENAI_API_KEY` in `.env` → fix and `./deploy.sh` |
| Backend healthcheck never passes | check `docker compose logs backend`; confirm `Main Data.xlsx` was copied into the image |
| Build OOM-killed | low RAM → add swap (`fallocate -l 2G /swapfile ...`) or build elsewhere |
| Can't reach site | check `ufw status` **and** Contabo panel firewall for port 80 |
| `.env` values ignored | remove spaces around `=`; values must be `KEY=value` |

## Appendix B — Copy code without git

From your Windows machine (PowerShell), using `scp`:

```powershell
scp -r "d:\Office Research\RWA with UI" deploy@91.230.110.121:~/rwa
```

Exclude `node_modules`, `.venv`, `.angular`, `dist` first to keep it small, or
just let `.dockerignore` handle them at build time (they won't be used anyway).
