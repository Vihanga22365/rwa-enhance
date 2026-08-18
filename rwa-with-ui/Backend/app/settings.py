"""Filesystem paths and process-level settings.

Every path is resolved from BACKEND_ROOT rather than the current working
directory, so the app behaves the same whether it is started from Backend/,
from the repo root, or from inside a container.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Backend/app/settings.py -> Backend/
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Load Backend/.env first, then fall back to a repo-root .env (the Docker
# Compose setup keeps one .env next to docker-compose.yml).
load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(BACKEND_ROOT.parent / ".env")


def _path_from_env(var: str, default: Path) -> Path:
    """Read a path override from the environment, resolved against BACKEND_ROOT."""
    raw = os.getenv(var, "").strip()
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    return candidate if candidate.is_absolute() else BACKEND_ROOT / candidate


# --- Data ---------------------------------------------------------------
# Mockup source tables. One sheet per table the agents can query.
SOURCE_TABLES_FILE = _path_from_env(
    "RWA_SOURCE_TABLES_FILE", BACKEND_ROOT / "data" / "Main Data.xlsx"
)

# The decision trees: one row per issue type, "Check Steps" holds the tree JSON.
DECISION_TREE_FILE = _path_from_env(
    "RWA_DECISION_TREE_FILE",
    BACKEND_ROOT / "docs" / "decision-trees" / "Issue Types and Steps.xlsx",
)

# --- LLM ----------------------------------------------------------------
LLM_CONFIG_FILE = _path_from_env("RWA_LLM_CONFIG_FILE", BACKEND_ROOT / "config" / "llm.yaml")

# --- API ----------------------------------------------------------------
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "false").lower() in ("1", "true", "yes")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
    if origin.strip()
]

# Guard against runaway tree traversal: the orchestrator loops itself through
# the decision tree, so this is the only hard stop on the agent loop.
#
# Each check step costs at least 2 tool round-trips (get_check_step_to_process,
# then get_prompt_using_table_name + a table tool), and each round-trip is 2
# recursion units (a model turn + a tool turn) in LangGraph's counting. Trees
# can run up to ~25 sequential steps, so a full traversal can need on the
# order of 25 * 4-6 = 100-150 units before any retries. 300 gives headroom.
AGENT_RECURSION_LIMIT = int(os.getenv("RWA_AGENT_RECURSION_LIMIT", "300"))

# --- Tracing ------------------------------------------------------------
# Only enable LangSmith when a key is actually configured; otherwise every
# request emits noisy auth errors against an empty key.
_langsmith_key = os.getenv("LANGSMITH_API_KEY", "").strip()
os.environ["LANGSMITH_TRACING"] = "true" if _langsmith_key else "false"
os.environ["LANGSMITH_ENDPOINT"] = os.getenv(
    "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
)
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Explainability")
