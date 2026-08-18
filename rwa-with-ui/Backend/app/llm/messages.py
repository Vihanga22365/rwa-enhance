"""Flattens LLM response content to plain text.

Classic chat models return `response.content` as a string. Reasoning models
called through /v1/responses (see api: responses in config/llm.yaml) return a
list of content blocks instead - typically `{"type": "text", "text": "..."}`
plus non-text blocks for reasoning summaries. Every place that reads
`.content` needs to handle both shapes, so it lives here once.
"""

from __future__ import annotations

from typing import Any


def message_text(content: Any) -> str:
    """Return the plain-text portion of a message's content, either shape."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(part for part in parts if part)
    return "" if content is None else str(content)
