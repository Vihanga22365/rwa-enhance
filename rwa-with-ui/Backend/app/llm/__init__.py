"""OpenAI model configuration and client construction.

Agents never construct a model directly; they call `get_llm("<role>")` so the
model id and thinking level stay in config/llm.yaml.
"""

from app.llm.config import KNOWN_ROLES, LLMConfigError, LLMSettings, get_llm_settings
from app.llm.factory import MissingAPIKeyError, get_llm, reset_cache

__all__ = [
    "KNOWN_ROLES",
    "LLMConfigError",
    "LLMSettings",
    "MissingAPIKeyError",
    "get_llm",
    "get_llm_settings",
    "reset_cache",
]
