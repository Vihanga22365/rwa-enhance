"""One data agent per source table.

Registry of every table that currently has an agent. To add another table:

  1. write its extraction prompt in app/prompts/table_agents.py and register it
     in EXTRACTION_PROMPTS,
  2. add a schema prefix there too,
  3. create a module here with its TableAgentSpec,
  4. append the spec to REGISTERED_SPECS below.

The orchestrator picks up whatever is in REGISTERED_SPECS, so no other file
needs to change.

Two of the six tables are wired up today. The other four
(dsft_conc_txn_result, dsft_conc_result_txn_map, dsft_conc_result,
dsft_fi_base_subassetclass) are loaded by app/data/tables.py but have neither
an extraction prompt nor an agent, so the orchestrator cannot reach them.
"""

from langchain_core.tools import BaseTool

from app.agents.table_agents.base import TableAgentSpec, build_table_agent, build_table_tool
from app.agents.table_agents.mart import MART_SPEC
from app.agents.table_agents.mart_extn import MART_EXTN_SPEC

REGISTERED_SPECS: tuple[TableAgentSpec, ...] = (MART_SPEC, MART_EXTN_SPEC)


def build_all_table_tools() -> list[BaseTool]:
    """Build every registered table agent and return them as orchestrator tools."""
    return [build_table_tool(spec) for spec in REGISTERED_SPECS]


__all__ = [
    "MART_EXTN_SPEC",
    "MART_SPEC",
    "REGISTERED_SPECS",
    "TableAgentSpec",
    "build_all_table_tools",
    "build_table_agent",
    "build_table_tool",
]
