"""Data agent for the Mart Extn table (OM_CDM_RWA_MTRC_EXTN).

Queried for the enrichment flags the later decision-tree steps branch on:
original_lgl_certainty_flg, ovr_imm_cancellable, incorp_cntry_assessment,
trade_type, lrm_flg, IS_DAILY_MARGN, swwr_flag, haircut_eligible_status.
"""

from app.agents.table_agents.base import TableAgentSpec
from app.prompts.table_agents import MART_EXTN_PREFIX

MART_EXTN_SPEC = TableAgentSpec(
    table_name="om_cdm_rwa_mtrc_extn",
    tool_name="mart_extn_tool",
    tool_description="Tool to extract data from the OM_CDM_RWA_MTRC_EXTN table.",
    schema_prompt=MART_EXTN_PREFIX,
)
