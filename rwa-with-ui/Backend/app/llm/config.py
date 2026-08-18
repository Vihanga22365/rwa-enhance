"""Reads config/llm.yaml into a typed settings object.

The YAML has a `defaults` block and optional `roles.<name>` overrides. This
module deep-merges the two so each agent gets its own resolved settings while
the file stays short.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

from app.settings import LLM_CONFIG_FILE

Role = Literal["classifier", "orchestrator", "table_agent", "conclusion"]

KNOWN_ROLES: tuple[str, ...] = ("classifier", "orchestrator", "table_agent", "conclusion")

# Values accepted for reasoning.effort. "none" is normalised to "not sent".
VALID_EFFORTS = {"none", "minimal", "low", "medium", "high"}
VALID_SUMMARIES = {"auto", "concise", "detailed"}
VALID_VERBOSITY = {"low", "medium", "high"}

# Which OpenAI endpoint to call. Reasoning models need /v1/responses when tools
# are involved; classic chat models use /v1/chat/completions.
VALID_APIS = {"responses", "chat_completions"}


class LLMConfigError(RuntimeError):
    """Raised when config/llm.yaml is missing, malformed, or has a bad value."""


@dataclass(frozen=True)
class LLMSettings:
    """Fully resolved settings for one agent role."""

    role: str
    provider: str
    model: str
    api: str = "responses"
    reasoning_effort: str | None = None
    reasoning_summary: str | None = None
    verbosity: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_seconds: float = 180.0
    max_retries: int = 3
    extra_params: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> str:
        """One-line human summary, used by the checker and startup logging."""
        bits = [f"model={self.model}", f"api={self.api}"]
        if self.reasoning_effort:
            bits.append(f"reasoning={self.reasoning_effort}")
        if self.verbosity:
            bits.append(f"verbosity={self.verbosity}")
        if self.temperature is not None:
            bits.append(f"temperature={self.temperature}")
        if self.max_tokens is not None:
            bits.append(f"max_tokens={self.max_tokens}")
        return f"{self.role}: " + ", ".join(bits)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge `override` onto `base`, recursing into nested dicts."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_choice(value: Any, allowed: set[str], label: str) -> str | None:
    """Normalise an optional enum-ish value, or raise with a useful message."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text or text == "none":
        return None
    if text not in allowed:
        raise LLMConfigError(
            f"{label} must be one of {sorted(allowed)} (or null), got {value!r}. "
            f"Fix it in {LLM_CONFIG_FILE}."
        )
    return text


def load_raw_config(path: Path | None = None) -> dict[str, Any]:
    """Parse the YAML file with clear errors for the common failure modes."""
    config_path = path or LLM_CONFIG_FILE
    if not config_path.exists():
        raise LLMConfigError(
            f"LLM config not found at {config_path}. Copy config/llm.yaml back into "
            f"place, or point RWA_LLM_CONFIG_FILE at your own file."
        )
    try:
        parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise LLMConfigError(f"{config_path} is not valid YAML: {exc}") from exc

    if not isinstance(parsed, dict):
        raise LLMConfigError(f"{config_path} must contain a YAML mapping at the top level.")
    return parsed


@lru_cache(maxsize=None)
def get_llm_settings(role: str = "orchestrator") -> LLMSettings:
    """Resolve settings for one agent role (defaults merged with role override).

    Cached: the config file is read once per process. Restart the API after
    editing config/llm.yaml.
    """
    raw = load_raw_config()

    provider = str(raw.get("provider", "openai")).strip().lower()
    if provider != "openai":
        raise LLMConfigError(
            f"provider {provider!r} is not supported; this build is OpenAI-only. "
            f"Set `provider: openai` in {LLM_CONFIG_FILE}."
        )

    defaults = raw.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise LLMConfigError("`defaults` must be a mapping in the LLM config.")

    roles = raw.get("roles") or {}
    if not isinstance(roles, dict):
        raise LLMConfigError("`roles` must be a mapping in the LLM config.")

    override = roles.get(role) or {}
    if not isinstance(override, dict):
        raise LLMConfigError(f"`roles.{role}` must be a mapping (or empty).")

    merged = _deep_merge(defaults, override)

    model = str(merged.get("model", "")).strip()
    if not model:
        raise LLMConfigError(f"No `model` set for role {role!r} in {LLM_CONFIG_FILE}.")

    reasoning = merged.get("reasoning") or {}
    if not isinstance(reasoning, dict):
        raise LLMConfigError("`reasoning` must be a mapping with `effort` / `summary`.")

    extra = merged.get("extra_params") or {}
    if not isinstance(extra, dict):
        raise LLMConfigError("`extra_params` must be a mapping.")

    temperature = merged.get("temperature")
    max_tokens = merged.get("max_tokens")

    api = _validate_choice(merged.get("api", "responses"), VALID_APIS, "api") or "responses"

    return LLMSettings(
        role=role,
        provider=provider,
        model=model,
        api=api,
        reasoning_effort=_validate_choice(
            reasoning.get("effort"), VALID_EFFORTS, "reasoning.effort"
        ),
        reasoning_summary=_validate_choice(
            reasoning.get("summary"), VALID_SUMMARIES, "reasoning.summary"
        ),
        verbosity=_validate_choice(merged.get("verbosity"), VALID_VERBOSITY, "verbosity"),
        temperature=float(temperature) if temperature is not None else None,
        max_tokens=int(max_tokens) if max_tokens is not None else None,
        timeout_seconds=float(merged.get("timeout_seconds", 180)),
        max_retries=int(merged.get("max_retries", 3)),
        extra_params=dict(extra),
    )
