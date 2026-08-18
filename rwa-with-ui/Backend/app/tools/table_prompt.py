"""Tool: get the extraction prompt for a given table.

The orchestrator works out which table a check step refers to, then calls this
to get the table-specific instructions (which columns to filter on, which value
to pull). It passes the returned prompt straight into that table's agent.
"""

from __future__ import annotations

from app.prompts.table_agents import EXTRACTION_PROMPTS


def get_prompt_using_table_name(
    table_name: str, user_query: str, check_step_for_tool: str
) -> str | None:
    """
    Get the prompt dynamically for the given valid dataframe/table name
    Available dataframes are,
    * om_cdm_rwa_mtrc
    * om_cdm_rwa_mtrc_extn
    * dsft_conc_txn_result
    * dsft_conc_result_txn_map
    * dsft_conc_result
    * dsft_fi_base_subassetclass
    :param table_name: This is the name of the dataframe/table
    :param user_query: User query to filter the dataframe
    :param check_step_for_tool: Check step pass to the tool to process.
    :return: Prompt string for the given table name
    """
    template = EXTRACTION_PROMPTS.get(table_name)
    if not template:
        # Unknown table, or a table whose extraction prompt is not written yet.
        return None
    return template.format(filter_text=user_query, check_step=check_step_for_tool)
