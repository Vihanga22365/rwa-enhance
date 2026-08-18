"""Builds the ChatOpenAI clients the agents run on.

One entry point: `get_llm(role)`. Each agent asks for its own role so the
thinking level can be tuned per agent from config/llm.yaml.

Two details worth knowing:

* Parameters left null in the config are never sent. Reasoning models reject
  `temperature`, so silently defaulting it would break them.
* `reasoning_effort` / `verbosity` became first-class ChatOpenAI fields only in
  newer langchain-openai releases. We check what the installed version accepts
  and route anything it does not know through `model_kwargs`, so the config
  keeps working across versions.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI

from app.llm.config import LLMSettings, get_llm_settings


class MissingAPIKeyError(RuntimeError):
    """Raised when OPENAI_API_KEY is absent."""


def _supported_fields() -> set[str]:
    """Constructor fields the installed ChatOpenAI actually accepts."""
    fields = getattr(ChatOpenAI, "model_fields", None)
    if fields:
        return set(fields.keys())
    return set(getattr(ChatOpenAI, "__fields__", {}).keys())


def require_api_key() -> str:
    """Return OPENAI_API_KEY or explain exactly how to set it."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise MissingAPIKeyError(
            "OPENAI_API_KEY is not set. Create Backend/.env (copy .env.example) "
            "and add:  OPENAI_API_KEY=sk-..."
        )
    return api_key


def build_client_kwargs(settings: LLMSettings) -> dict[str, Any]:
    """Translate resolved settings into ChatOpenAI constructor kwargs."""
    supported = _supported_fields()

    kwargs: dict[str, Any] = {
        "model": settings.model,
        "timeout": settings.timeout_seconds,
        "max_retries": settings.max_retries,
    }
    passthrough: dict[str, Any] = {}

    # Reasoning models reject `reasoning_effort` alongside function tools on
    # /v1/chat/completions, and two of the four agents use tools. Routing to
    # /v1/responses is what the API itself recommends in that error.
    if settings.api == "responses" and "use_responses_api" in supported:
        kwargs["use_responses_api"] = True

    # Optional params: only included when the config actually sets them.
    optional: dict[str, Any] = {
        "reasoning_effort": settings.reasoning_effort,
        "verbosity": settings.verbosity,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }
    for name, value in optional.items():
        if value is None:
            continue
        if name in supported:
            kwargs[name] = value
        else:
            passthrough[name] = value

    # Reasoning summaries ride along on the `reasoning` object, not a flat field.
    if settings.reasoning_summary:
        passthrough["reasoning"] = {"summary": settings.reasoning_summary}

    passthrough.update(settings.extra_params)
    if passthrough:
        kwargs["model_kwargs"] = passthrough

    return kwargs


@lru_cache(maxsize=None)
def get_llm(role: str = "orchestrator") -> ChatOpenAI:
    """Return the (cached) chat model for an agent role.

    Cached per role so the four agents reuse one client each. Restart the
    process after editing config/llm.yaml.
    """
    settings = get_llm_settings(role)
    api_key = require_api_key()
    return ChatOpenAI(api_key=api_key, **build_client_kwargs(settings))


def reset_cache() -> None:
    """Drop cached clients and settings. Used by tests and the config checker."""
    get_llm.cache_clear()
    get_llm_settings.cache_clear()
