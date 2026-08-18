"""Shared construction for the per-table data agents.

Each source table gets its own pandas agent, given only that table's dataframe
and only that table's column list. The agent writes and executes real pandas
code to pull one field value, then is wrapped with `.as_tool()` so the
orchestrator can call it like any other tool.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from langchain_core.tools import BaseTool
from langchain_experimental.agents import create_pandas_dataframe_agent

from app.data.tables import get_table
from app.llm import get_llm
from app.prompts.table_agents import PANDAS_AGENT_SUFFIX


@dataclass(frozen=True)
class TableAgentSpec:
    """Everything needed to build one table's agent."""

    table_name: str  # sheet name in data/Main Data.xlsx
    tool_name: str  # name the orchestrator calls it by
    tool_description: str  # what the orchestrator sees when choosing a tool
    schema_prompt: str  # column list handed to the pandas agent


def build_table_agent(spec: TableAgentSpec, dataframe: pd.DataFrame | None = None):
    """Build the pandas agent for one table."""
    frame = dataframe if dataframe is not None else get_table(spec.table_name)
    return create_pandas_dataframe_agent(
        get_llm("table_agent"),
        frame,
        agent_type="tool-calling",
        verbose=True,
        # The agent executes generated pandas code. Safe here because the data
        # is a local mock workbook and the prompt is not user-controlled, but
        # this is the flag to revisit before pointing at real data.
        allow_dangerous_code=True,
        return_intermediate_steps=True,
        prefix=spec.schema_prompt,
        suffix=PANDAS_AGENT_SUFFIX,
        number_of_head_rows=1,
    )


def build_table_tool(spec: TableAgentSpec, dataframe: pd.DataFrame | None = None) -> BaseTool:
    """Build one table's agent and expose it as a tool for the orchestrator."""
    agent = build_table_agent(spec, dataframe)
    return agent.as_tool(name=spec.tool_name, description=spec.tool_description)
