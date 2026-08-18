"""Data agent for the Mart table (OM_CDM_RWA_MTRC).

Queried for the trade-level fields the early decision-tree steps check:
FDL_FX_AMT, NETG_AGR_ID, LGL_CERTAINTY_FLG.
"""

from app.agents.table_agents.base import TableAgentSpec
from app.prompts.table_agents import MART_PREFIX

MART_SPEC = TableAgentSpec(
    table_name="om_cdm_rwa_mtrc",
    tool_name="mart_tool",
    tool_description="Tool to extract data from the OM_CDM_RWA_MTRC table.",
    schema_prompt=MART_PREFIX,
)
