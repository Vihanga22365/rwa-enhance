"""Wires the agents into the two flows the API exposes.

Initial analysis (email submitted)
    classifier -> pick decision tree -> orchestrator walks it -> conclusion

Follow-up (user asks a question in chat)
    on a thread that already ran an initial analysis, the follow-up message
    is sent as-is on the same conversation thread - the orchestrator already
    remembers the full prior trace via its checkpointer (see
    app/agents/orchestrator.py), so resending the email or synthesizing a
    tree is unnecessary. On a cold thread (no prior /email-submit on this
    thread_id), falls back to a standalone one-step tree so the follow-up
    still works on its own.
"""

from __future__ import annotations

import json
import logging

from app.agents.classifier import NO_ISSUE_MATCHED
from app.agents.orchestrator import is_cold_thread, run_decision_tree
from app.data.decision_trees import NO_STEPS_FOUND, get_check_steps, list_issue_types
from app.prompts.orchestrator import ORCHESTRATOR_INPUT_TEMPLATE

logger = logging.getLogger(__name__)

INVALID_ISSUE_MESSAGE = "Please provide a valid issue type."
UNSUPPORTED_ISSUE_MESSAGE = "Issue type is not supported yet."


def _build_input(filter_text: str, check_steps: str) -> str:
    """Format the orchestrator's user message."""
    return ORCHESTRATOR_INPUT_TEMPLATE.format(
        filter_text=filter_text, check_steps=check_steps
    )


def run_initial_analysis(issue_type: str, email_content: str, *, thread_id: str) -> str:
    """Walk the decision tree for a classified issue type.

    Returns a plain message instead of a trace when the issue type has no
    decision tree defined.

    :param thread_id: conversation identifier (the caller's session_id),
        reused as the orchestrator's memory key so later follow-ups on the
        same thread can recall this traversal.
    """
    if issue_type == NO_ISSUE_MATCHED:
        return INVALID_ISSUE_MESSAGE

    supported = list_issue_types()
    if issue_type not in supported:
        logger.info(
            "No decision tree for issue type %r; defined trees: %s", issue_type, supported
        )
        return UNSUPPORTED_ISSUE_MESSAGE

    check_steps = get_check_steps(issue_type)
    if check_steps == NO_STEPS_FOUND:
        return UNSUPPORTED_ISSUE_MESSAGE

    # The workbook cell already holds JSON; json.dumps here matches the original
    # behaviour of passing it through as a quoted JSON string.
    input_content = _build_input(email_content, json.dumps(check_steps, indent=4))
    return run_decision_tree(input_content, thread_id=thread_id)


def run_follow_up(email_content: str, user_question: str, *, thread_id: str) -> str:
    """Continue the conversation on `thread_id` with a follow-up message.

    On a warm thread, the orchestrator already has the full prior trace in
    its checkpointed history, so the raw follow-up text is sent as-is; its
    prompt (app/prompts/orchestrator.py) is what decides whether this is an
    ad hoc check, a human-directed re-scoping, or a what-if simulation. On a
    cold thread (no prior traversal on this thread_id), falls back to a
    standalone one-step tree so the follow-up still works by itself.
    """
    if is_cold_thread(thread_id):
        single_step_tree = json.dumps({"1": user_question}, indent=4)
        input_content = _build_input(email_content, single_step_tree)
    else:
        input_content = user_question

    return run_decision_tree(input_content, thread_id=thread_id)
