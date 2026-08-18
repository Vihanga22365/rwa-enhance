"""Request and response models for the HTTP API.

`ApiMessage.label` carries the conclusion agent's summary; the Angular UI shows
it as the collapsed header and `content` (the full traversal trace) as the body.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    label: str | None = None


class EmailSubmitRequest(BaseModel):
    input_text: str = Field(min_length=1)
    session_id: str | None = None


class FollowUpRequest(BaseModel):
    input_text: str | None = None
    user_chat_input: str = Field(min_length=1)
    issue_type: str | None = None
    session_id: str | None = None


class AgentResponse(BaseModel):
    session_id: str
    issue_type: str
    messages: list[ApiMessage]
