"""In-process conversation store.

Holds the original email and classified issue type per session so follow-up
requests do not have to resend them.

This is a plain dict in memory: sessions are lost on restart and are NOT shared
between workers. That is why the API runs with a single uvicorn worker. Swap
this module for Redis if you ever need to scale out.
"""

from __future__ import annotations

import uuid
from threading import Lock

from app.api.schemas import ApiMessage

_lock = Lock()
_store: dict[str, dict[str, object]] = {}


def get_or_create_session_id(session_id: str | None) -> str:
    """Reuse the caller's session id, or mint a new one."""
    if session_id and session_id.strip():
        return session_id.strip()
    return str(uuid.uuid4())


def upsert(
    session_id: str,
    *,
    input_text: str | None = None,
    issue_type: str | None = None,
    messages: list[ApiMessage] | None = None,
) -> None:
    """Update a session, appending any new messages."""
    with _lock:
        state = _store.get(session_id, {"input_text": "", "issue_type": "", "messages": []})

        if input_text is not None:
            state["input_text"] = input_text
        if issue_type is not None:
            state["issue_type"] = issue_type
        if messages:
            existing = state.get("messages", [])
            existing.extend([message.model_dump() for message in messages])
            state["messages"] = existing

        _store[session_id] = state


def get_value(session_id: str, key: str) -> str:
    """Read one field from a session, empty string when absent."""
    with _lock:
        state = _store.get(session_id, {})
        value = state.get(key, "")
    return str(value) if value is not None else ""


def clear() -> None:
    """Drop all sessions. Used by tests."""
    with _lock:
        _store.clear()
