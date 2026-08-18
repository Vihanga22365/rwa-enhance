"""Prompts for the per-table pandas agents (app/agents/table_agents/).

Two distinct kinds live here:

1. SCHEMA prompts (`*_PREFIX` / `PANDAS_AGENT_SUFFIX`) configure the pandas
   agent itself. They tell it which columns exist in its dataframe. Passed to
   `create_pandas_dataframe_agent` when the agent is built.

2. EXTRACTION prompts (`PANDAS_AGENT_PROMPT_*`) are handed to an already-built
   agent at call time by the `get_prompt_using_table_name` tool. They describe
   how to filter the table for the counterparty/security in question and which
   field the current check step needs.

Four of the six tables have no extraction prompt written yet. They are empty
strings, matching the original code; the orchestrator has no tool for those
tables either, so they are unreachable until both are filled in.
"""

# =======================================================================
#  1. Schema prompts - passed when the pandas agent is constructed
# =======================================================================

MART_PREFIX = (
    "You are working with a pandas dataframe in Python. The name of the dataframe is `df`.\n"
    "Here are the available important columns and data types in the df:\n"
    "  * 'OBLG_ID' - Integer - The id of the organization.\n"
    "  * 'SCR_ID' - String - Security Identifier.\n"
    "  * 'BUY_SELL_IND' - String - Buy or sell indicator\n"
    "  * 'BAL_TYP_CD' - Integer - Balance type code.\n"
    "  * 'FDL_FX_AMT' - Float\n"
    "  * 'NETG_AGR_ID' - Integer\n"
    "  * 'LGL_CERTAINTY_FLG' - String - Legal certainty flag.\n"
    "  * 'src_txn_id' - String\n"
)

MART_EXTN_PREFIX = (
    "You are working with a pandas dataframe in Python. The name of the dataframe is `df`.\n"
    "Here are the available important columns in the df:\n"
    "- 'principal_gfcid' - Integer - Principal GFCID(OBLG_ID).\n"
    "- 'original_lgl_certainty_flg' - String\n"
    "- 'ovr_imm_cancellable' - String\n"
    "- 'incorp_cntry_assessment' - String\n"
    "- 'trade_type' - String\n"
    "- 'stale_prc_flg_2days' - String\n"
    "- 'stale_prc_flg_6mths' - String\n"
    "- 'bal_typ_cd' - String - Balance type code.\n"
    "- 'lrm_flg' - String\n"
    "- 'IS_DAILY_MARGN' - String\n"
    "- 'swwr_flag' - String\n"
    "- 'swwr_recovery_rate' - Float\n"
    "- 'haircut_eligible_status' - String\n"
)

# `{df_head}` is filled in by create_pandas_dataframe_agent.
PANDAS_AGENT_SUFFIX = "This is the result of `print(df.head())`:\n{df_head}"


# =======================================================================
#  2. Extraction prompts - handed to the agent per check step
# =======================================================================

PANDAS_AGENT_PROMPT_MART = """You are an agent tasked with extracting specific values for given fields/parameters from a dataframe.

##INSTRUCTIONS TO make THE PANDAS QUERY:
#Step 01: Identify the Filtering Column and Value from the Filter text.
- Extract the value for the column 'OBLG_ID'(GFCID) from the provided Filter text.
- Filter the dataframe using the extracted value for 'OBLG_ID'.
- Extract the value for the column 'SCR_ID'(Security ID) or any other column if provided in Filter text.
- Filter the dataframe using the extracted value for those additional columns.
#Step 02: Apply additional filters, using sensible defaults only when the Check step
itself does not name a different value or a broader population to inspect:
    - If the Check step does not specify a value for 'BUY_SELL_IND', use the default
      'BUY_SELL_IND' == 'B'. If the Check step explicitly asks about a different value,
      about all values, or about consistency/mismatch across values, do NOT apply this
      default - filter (or omit filtering) exactly as the Check step describes.
    - If the Check step does not specify a value for 'BAL_TYP_CD', use the default
      'BAL_TYP_CD' in [15, 16]. If the Check step explicitly names a different balance
      type (e.g. 17), asks about a specific balance type, or asks to check for the
      presence/absence of a particular balance type, do NOT apply this default -
      filter exactly as the Check step describes instead.
#Step 03: Identify the parameter(s) to extract from the Check step.
- Determine the name(s) of the parameter(s) (i.e., columns) that need to be extracted from the dataframe based on the Check step.
#Step 04: Write a Pandas query to retrieve specific value(s)
- Construct a Pandas query to extract the value(s) for the parameter(s) identified in Step 3.
- Ensure the query retrieves only the relevant value(s) for the specified parameter(s) and does not return entire columns or rows of the dataframe.

Filter text: {filter_text}
Check step: {check_step}

##Key Considerations:
- Focus on extracting only the required parameter(s) as specified in the Check step. Avoid unnecessary data retrieval.
- You will be evaluated on how well you only extract the value of the parameter and not any condition.
- Write concise and efficient Pandas queries to extract the relevant parameter value.

##Example Queries:
1. Filter text: RE: GFCID '1123456648'dropped collateral
Check step: Extract value for 'LGL_CERTAINTY_FLG' from the dataframe using the Pandas query.

Generated Pandas query: df[(df['OBLG_ID'] == 1123456648) & (df['BUY_SELL_IND'] == 'B') & (df['BAL_TYP_CD'].isin([15, 16]))]['LGL_CERTAINTY_FLG'].values[0]
Like the example, always try to extract the value for the requested parameter from the dataframe using the Pandas query.
"""

PANDAS_AGENT_PROMPT_MART_EXTN = """You are an agent tasked with extracting specific values for given fields/parameters from a dataframe.

##INSTRUCTIONS TO make THE PANDAS QUERY:
#Step 01: Identify the Filtering Column and Value from the Filter text.
- Extract the value for the column 'principal_gfcid'(GFCID) from the provided Filter text.
- Filter the dataframe using the extracted value for 'principal_gfcid'.
#Step 02: Apply additional filters, using a sensible default only when the Check step
itself does not name a different value or a broader population to inspect:
    - If the Check step does not specify a value for 'bal_typ_cd', use the default
      'bal_typ_cd' in [15, 16]. If the Check step explicitly names a different balance
      type, or asks about a specific balance type / presence-absence check, do NOT
      apply this default - filter exactly as the Check step describes instead.
#Step 03: Identify the parameter(s) to extract from the Check step.
- Determine the name(s) of the parameter(s) (i.e., columns) that need to be extracted from the dataframe based on the Check step.
#Step 04: Write a Pandas query to retrieve specific value(s)
- Construct a Pandas query to extract the value(s) for the parameter(s) identified in Step 3.
- Ensure the query retrieves only the relevant value(s) for the specified parameter(s) and does not return entire columns or rows of the dataframe.

Filter text: {filter_text}
Check step: {check_step}

##Key Considerations:
- Focus on extracting only the required parameter(s) as specified in the Check step. Avoid unnecessary data retrieval.
- Write concise and efficient Pandas queries to achieve the desired result.

##Example Queries:
1. Filter text: RE: GFCID '1123456648'dropped collateral
Check step: Extract value for `original_lgl_certainty_flg` from the dataframe using the Pandas query.

Generated Pandas query: df[(df['principal_gfcid'] == 1123456648) & (df['bal_typ_cd'].isin([15, 16]))]['original_lgl_certainty_flg'].values[0]
Like the example, always try to extract the value for the requested parameter from the dataframe using the Pandas query.
"""

# --- Not yet written ---------------------------------------------------
# Fill these in (and add a matching agent in app/agents/table_agents/) to make
# the remaining four tables queryable.
PANDAS_AGENT_PROMPT_DSFT_TXN_RESULT = ""
PANDAS_AGENT_PROMPT_TXN_MAP = ""
PANDAS_AGENT_PROMPT_DSFT_CONC_RESULT = ""
PANDAS_AGENT_PROMPT_DSFT_BASE_SUBASSETCLASS = ""


# Table name -> extraction prompt template. Used by the
# `get_prompt_using_table_name` tool.
EXTRACTION_PROMPTS: dict[str, str] = {
    "om_cdm_rwa_mtrc": PANDAS_AGENT_PROMPT_MART,
    "om_cdm_rwa_mtrc_extn": PANDAS_AGENT_PROMPT_MART_EXTN,
    "dsft_conc_txn_result": PANDAS_AGENT_PROMPT_DSFT_TXN_RESULT,
    "dsft_conc_result_txn_map": PANDAS_AGENT_PROMPT_TXN_MAP,
    "dsft_conc_result": PANDAS_AGENT_PROMPT_DSFT_CONC_RESULT,
    "dsft_fi_base_subassetclass": PANDAS_AGENT_PROMPT_DSFT_BASE_SUBASSETCLASS,
}
