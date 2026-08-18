"""Conclusion agent.

Last agent in the pipeline. Reads the orchestrator's full step-by-step trace
and writes the 2-3 sentence summary that the UI shows as the collapsed header
above the expandable trace.

A single LLM call, no tools.
"""

from __future__ import annotations

import logging

from app.llm import get_llm
from app.llm.messages import message_text
from app.prompts.conclusion import FINAL_CONCLUSION_PROMPT

logger = logging.getLogger(__name__)


class ConclusionError(RuntimeError):
    """Raised when the final conclusion could not be generated."""


def generate_final_conclusion(input_text: str, validation_steps: str) -> str:
    """Summarise the traversal trace for the end user."""
    prompt = FINAL_CONCLUSION_PROMPT.format(
        input_text=input_text, validation_steps=validation_steps
    )

    try:
        response = get_llm("conclusion").invoke(prompt)
    except Exception as exc:
        logger.exception("Final conclusion LLM call failed")
        raise ConclusionError(f"Failed to generate the final conclusion: {exc}") from exc

    conclusion = message_text(response.content).strip()
    if not conclusion:
        raise ConclusionError("Final conclusion returned an empty response.")

    return conclusion
