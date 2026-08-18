# RWA with UI — Local Setup Guide

Two apps:

- **Backend**: FastAPI service (`http://127.0.0.1:8000`) — see [Backend/README.md](Backend/README.md)
- **Frontend**: Angular UI (`http://localhost:4200`)

The frontend calls the backend at `http://<host>:8000` in dev, and at the same
origin via nginx in the Docker deployment.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm

## 1) Backend

```bash
cd Backend && ./scripts/setup.sh
```

That creates `.venv`, installs dependencies, and writes a `Backend/.env`.
Add your key to it:

```
OPENAI_API_KEY=sk-...
```

The model and thinking level are **not** in `.env` — they live in
[`Backend/config/llm.yaml`](Backend/config/llm.yaml). Check both are valid
before starting:

```bash
cd Backend && ./.venv/bin/python -m app.llm.check
```

Run it:

```bash
cd Backend && ./scripts/run_api.sh
```

Health check: `http://127.0.0.1:8000/health`
Live settings: `http://127.0.0.1:8000/api/rwa/config`
API docs: `http://127.0.0.1:8000/docs`

### On Windows

```bat
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python -m app.llm.check
uvicorn app.main:app --port 8000 --reload
```

## 2) Frontend

```bash
cd Frontend
npm install
npm start
```

Open `http://localhost:4200`, then go to **RWA Agent**. Paste one of the
examples from [`Backend/docs/sample-emails/`](Backend/docs/sample-emails/) and
click Submit.

## Tests

```bash
cd Backend && ./.venv/bin/python -m pytest tests -q
```

## Docker

```bash
cp .env.example .env   # add OPENAI_API_KEY
docker compose up -d --build
```

See [DEPLOYMENT.md](DEPLOYMENT.md).
