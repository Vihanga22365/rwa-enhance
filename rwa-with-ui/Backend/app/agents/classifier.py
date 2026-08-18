"""Issue-classification agent.

First agent in the pipeline. Maps the inbound email to one of the known issue
types, which selects the decision tree the orchestrator will then walk.

The set of issue types is read from the decision-tree workbook at call time
(app/data/decision_trees.py:list_issue_types()) rather than hardcoded, so a
new workbook with different categories works with no code change here.

A single LLM call, no tools.
"""

from __future__ import annotations

import logging

from app.data.decision_trees import list_issue_types
from app.llm import get_llm
from app.llm.messages import message_text
from app.prompts.classification import ISSUE_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

NO_ISSUE_MATCHED = "No Issue Matched"


class ClassificationError(RuntimeError):
    """Raised when the issue type could not be determined."""


def _format_issue_type_list(issue_types: list[str]) -> str:
    return "\n".join(f"{i}. {name}" for i, name in enumerate(issue_types, start=1))


def classify_issue_type(input_text: str) -> str:
    """Return the issue type for an email, or NO_ISSUE_MATCHED."""
    issue_types = list_issue_types()
    if not issue_types:
        logger.warning("No issue types defined in the decision-tree workbook.")
        return NO_ISSUE_MATCHED

    prompt = ISSUE_CLASSIFICATION_PROMPT.format(
        issue_type_list=_format_issue_type_list(issue_types),
        input_text=input_text,
    )
    logger.info("Classifying issue type for input of %d chars", len(input_text))

    try:
        response = get_llm("classifier").invoke(prompt)
    except Exception as exc:
        logger.exception("Issue classification LLM call failed")
        raise ClassificationError(f"Failed to classify issue type: {exc}") from exc

    issue_type = message_text(response.content).strip()
    if not issue_type:
        raise ClassificationError("Issue classification returned an empty response.")

    if issue_type != NO_ISSUE_MATCHED and issue_type not in issue_types:
        logger.warning(
            "Classifier returned %r, which is not a known issue type %s; "
            "treating as no match.",
            issue_type,
            issue_types,
        )
        return NO_ISSUE_MATCHED

    logger.info("Classified issue type: %s", issue_type)
    return issue_type
