"""HTTP routes.

    GET  /health              liveness probe
    GET  /api/rwa/config      resolved LLM settings + known issue types
    POST /api/rwa/email-submit  classify, walk the decision tree, summarise
    POST /api/rwa/follow-up     run one user-supplied check
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.agents import (
    classify_issue_type,
    generate_final_conclusion,
    run_follow_up,
    run_initial_analysis,
)
from app.api import sessions
from app.api.schemas import (
    AgentResponse,
    ApiMessage,
    EmailSubmitRequest,
    FollowUpRequest,
)
from app.data.decision_trees import list_issue_types
from app.llm import KNOWN_ROLES, get_llm_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/rwa/config")
def config() -> dict[str, object]:
    """What the backend is actually running with. Handy for debugging the UI."""
    return {
        "llm": {role: get_llm_settings(role).describe() for role in KNOWN_ROLES},
        "issue_types_with_decision_trees": list_issue_types(),
    }


@router.post("/api/rwa/email-submit", response_model=AgentResponse)
def submit_email(payload: EmailSubmitRequest) -> AgentResponse:
    input_text = payload.input_text.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="input_text is required")

    session_id = sessions.get_or_create_session_id(payload.session_id)

    try:
        issue_type = classify_issue_type(input_text)
        agent_response = run_initial_analysis(issue_type, input_text, thread_id=session_id)
        final_conclusion = generate_final_conclusion(input_text, agent_response)
    except Exception as exc:
        logger.exception("email-submit failed")
        raise HTTPException(
            status_code=500, detail=f"Failed to process email submit: {exc}"
        ) from exc

    messages = [
        ApiMessage(role="assistant", content=f"Classified Issue Type: {issue_type}"),
        ApiMessage(role="assistant", content=agent_response, label=final_conclusion),
    ]

    sessions.upsert(
        session_id, input_text=input_text, issue_type=issue_type, messages=messages
    )

    return AgentResponse(session_id=session_id, issue_type=issue_type, messages=messages)


@router.post("/api/rwa/follow-up", response_model=AgentResponse)
def follow_up(payload: FollowUpRequest) -> AgentResponse:
    user_chat_input = payload.user_chat_input.strip()
    if not user_chat_input:
        raise HTTPException(status_code=400, detail="user_chat_input is required")

    session_id = sessions.get_or_create_session_id(payload.session_id)
    input_text = (payload.input_text or "").strip() or sessions.get_value(
        session_id, "input_text"
    )
    issue_type = (payload.issue_type or "").strip() or sessions.get_value(
        session_id, "issue_type"
    )

    if not issue_type:
        if not input_text:
            raise HTTPException(
                status_code=400,
                detail="Provide input_text first through email-submit before follow-up",
            )
        issue_type = classify_issue_type(input_text)

    try:
        agent_response = run_follow_up(input_text, user_chat_input, thread_id=session_id)
        final_conclusion = generate_final_conclusion(input_text, agent_response)
    except Exception as exc:
        logger.exception("follow-up failed")
        raise HTTPException(
            status_code=500, detail=f"Failed to process follow-up: {exc}"
        ) from exc

    messages = [
        ApiMessage(role="user", content=user_chat_input),
        ApiMessage(role="assistant", content=agent_response, label=final_conclusion),
    ]

    sessions.upsert(
        session_id, input_text=input_text, issue_type=issue_type, messages=messages
    )

    # Only the assistant reply goes back; the UI already rendered the user turn.
    return AgentResponse(
        session_id=session_id, issue_type=issue_type, messages=[messages[1]]
    )
