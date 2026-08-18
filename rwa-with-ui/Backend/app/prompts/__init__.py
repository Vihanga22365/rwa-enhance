"""Every prompt in the application, one module per agent family.

classification.py  -> app/agents/classifier.py
orchestrator.py    -> app/agents/orchestrator.py
conclusion.py      -> app/agents/conclusion.py
table_agents.py    -> app/agents/table_agents/ and app/tools/table_prompt.py
"""

from app.prompts.classification import ISSUE_CLASSIFICATION_PROMPT
from app.prompts.conclusion import FINAL_CONCLUSION_PROMPT
from app.prompts.orchestrator import ORCHESTRATOR_INPUT_TEMPLATE, ORCHESTRATOR_PROMPT
from app.prompts.table_agents import (
    EXTRACTION_PROMPTS,
    MART_EXTN_PREFIX,
    MART_PREFIX,
    PANDAS_AGENT_SUFFIX,
)

__all__ = [
    "EXTRACTION_PROMPTS",
    "FINAL_CONCLUSION_PROMPT",
    "ISSUE_CLASSIFICATION_PROMPT",
    "MART_EXTN_PREFIX",
    "MART_PREFIX",
    "ORCHESTRATOR_INPUT_TEMPLATE",
    "ORCHESTRATOR_PROMPT",
    "PANDAS_AGENT_SUFFIX",
]
