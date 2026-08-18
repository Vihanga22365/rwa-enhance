"""Tool: fetch one step out of the decision tree.

This is how the orchestrator navigates the tree. It picks the step number
itself (based on the branching instructions written into the previous step's
text) and calls this tool to pull that step's description.

The tool is a plain dictionary lookup - all branching intelligence lives in the
agent, not here.
"""

from __future__ import annotations

import json
from typing import Annotated


def get_check_step_to_process(
    step_number: Annotated[str, "Step Number to retrieve from the check steps json"],
    check_steps: Annotated[str, "JSON string with all the Check steps"],
) -> str:
    """
    Get the check step to process next based on the step number and check steps provided.
    :param step_number: Step Number to retrieve from the check steps json.
    :param check_steps: Full JSON string with steps.
    :return: Check step to process next
    """
    if isinstance(check_steps, str):
        try:
            check_steps = json.loads(check_steps)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided for check_steps")

    if not isinstance(check_steps, dict):
        raise ValueError("check_steps must decode to a JSON object of step_number -> text")

    description = check_steps.get(str(step_number))
    if description is None:
        available = ", ".join(sorted(check_steps.keys()))
        return (
            f"No step {step_number!r} exists in this decision tree. "
            f"Available steps: {available}"
        )
    return description
