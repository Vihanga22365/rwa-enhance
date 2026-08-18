"""Loads the scenario decision trees.

Each issue type has one decision tree, stored in
docs/decision-trees/Issue Types and Steps.xlsx as a two-column sheet:

    Issue Type   | Check Steps
    -------------+------------------------------------------------------
    <name>       | <JSON string: {"1": "...", "3.1": "...", ...}>

Keys encode the tree shape ("3" has sub-steps "3.1" ... "3.5"); the branching
rules and the stopping criteria live in the English text of each step, which is
what the orchestrator agent reads and acts on.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.settings import DECISION_TREE_FILE

ISSUE_TYPE_COLUMN = "Issue Type"
CHECK_STEPS_COLUMN = "Check Steps"

NO_STEPS_FOUND = "No Check Steps Found"


class DecisionTreeError(RuntimeError):
    """Raised when the decision-tree workbook is missing or malformed."""


@lru_cache(maxsize=1)
def _load_sheet() -> pd.DataFrame:
    if not DECISION_TREE_FILE.exists():
        raise DecisionTreeError(
            f"Decision tree workbook not found at {DECISION_TREE_FILE}. "
            f"Set RWA_DECISION_TREE_FILE to override the location."
        )
    frame = pd.read_excel(DECISION_TREE_FILE)
    missing = {ISSUE_TYPE_COLUMN, CHECK_STEPS_COLUMN} - set(frame.columns)
    if missing:
        raise DecisionTreeError(
            f"{DECISION_TREE_FILE} is missing column(s): {', '.join(sorted(missing))}"
        )
    return frame


def list_issue_types() -> list[str]:
    """Every issue type that currently has a decision tree defined."""
    return [str(value) for value in _load_sheet()[ISSUE_TYPE_COLUMN].tolist()]


def get_check_steps(issue_type: str) -> str:
    """Return the raw check-steps JSON string for an issue type.

    Returns the NO_STEPS_FOUND sentinel when the issue type has no tree, which
    is how the previous implementation signalled this.
    """
    frame = _load_sheet()
    matches = frame[frame[ISSUE_TYPE_COLUMN] == issue_type][CHECK_STEPS_COLUMN].values
    if len(matches) == 0:
        return NO_STEPS_FOUND
    return str(matches[0])


def reset_cache() -> None:
    """Force the workbook to be re-read on the next call."""
    _load_sheet.cache_clear()
