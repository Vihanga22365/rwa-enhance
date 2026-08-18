"""The agents.

classifier.py     email -> issue type (selects which decision tree to walk)
orchestrator.py   walks the decision tree, fetching data and deciding branches
conclusion.py     trace -> 2-3 sentence summary for the UI
table_agents/     one pandas agent per source table, exposed to the
                  orchestrator as tools
pipeline.py       wires the above into the two flows the API exposes
"""

from app.agents.classifier import NO_ISSUE_MATCHED, ClassificationError, classify_issue_type
from app.agents.conclusion import ConclusionError, generate_final_conclusion
from app.agents.orchestrator import OrchestrationError, build_orchestrator, run_decision_tree
from app.agents.pipeline import run_follow_up, run_initial_analysis

__all__ = [
    "NO_ISSUE_MATCHED",
    "ClassificationError",
    "ConclusionError",
    "OrchestrationError",
    "build_orchestrator",
    "classify_issue_type",
    "generate_final_conclusion",
    "run_decision_tree",
    "run_follow_up",
    "run_initial_analysis",
]
