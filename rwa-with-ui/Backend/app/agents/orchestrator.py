"""Orchestrator agent - the one that walks the decision tree.

This is a single LangGraph ReAct agent. It receives the filter text (the
email) plus the whole decision tree as JSON, and then loops itself through the
tree:

    get_check_step_to_process(step_number)   pick and fetch the next step
    get_prompt_using_table_name(table, ...)  get that table's extraction prompt
    mart_tool / mart_extn_tool               run the query, get one value
    -> judge Pass/Fail, decide the next step number, repeat

Step selection, branching and the stopping criterion are all decided by the
model from the prompt text; there is no coded state machine. The only hard
stop is AGENT_RECURSION_LIMIT.

Conversation memory: the agent is built once per process (see
build_orchestrator, cached) with a shared InMemorySaver checkpointer. Each
caller passes its own `thread_id` (the API layer uses the session_id) to
run_decision_tree; invoking again with the same thread_id resumes from that
conversation's full prior history - every step already walked, every value
already fetched - so a follow-up does not need to resend the original email
or decision tree. This is what makes ad hoc follow-ups, human-directed checks,
and what-if simulations (see app/prompts/orchestrator.py) possible: the model
can see exactly where a previous turn stopped and continue from there.

Note on naming: the agent is called "supervisor" in its prompt and was called
`data_extraction_agent` in the original code. It is one agent doing both jobs.
The two-tier langgraph_supervisor design (a supervisor above a separate
data-extraction agent) exists only as unused prompts in
app/prompts/orchestrator.py.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.messages.utils import filter_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from app.agents.table_agents import build_all_table_tools
from app.llm import get_llm
from app.llm.messages import message_text
from app.prompts.orchestrator import ORCHESTRATOR_PROMPT
from app.settings import AGENT_RECURSION_LIMIT
from app.tools import get_check_step_to_process, get_prompt_using_table_name

logger = logging.getLogger(__name__)

# Must match the name filtered on when collecting the trace below.
ORCHESTRATOR_AGENT_NAME = "orchestrator_agent"


class OrchestrationError(RuntimeError):
    """Raised when the traversal produced no usable output."""


@lru_cache(maxsize=1)
def _checkpointer() -> InMemorySaver:
    """One shared in-memory checkpoint store for the whole process.

    Internally keyed by thread_id, so many concurrent conversations are safe
    against a single instance. Lost on restart, not shared across workers -
    matches the existing in-memory session store (app/api/sessions.py) and
    introduces no new constraint.
    """
    return InMemorySaver()


@lru_cache(maxsize=1)
def build_orchestrator():
    """Construct the ReAct agent with its tools, once per process.

    Building this is expensive (it spins up two create_pandas_dataframe_agent
    instances), so it is cached rather than rebuilt on every request as
    before. Conversation isolation happens entirely via the `thread_id`
    passed at invoke time, not by rebuilding the agent.
    """
    tools = [
        get_check_step_to_process,
        get_prompt_using_table_name,
        *build_all_table_tools(),
    ]
    return create_react_agent(
        model=get_llm("orchestrator"),
        tools=tools,
        prompt=ORCHESTRATOR_PROMPT,
        name=ORCHESTRATOR_AGENT_NAME,
        checkpointer=_checkpointer(),
    )


def reset_cache() -> None:
    """Drop the cached orchestrator and checkpointer. Used by tests."""
    build_orchestrator.cache_clear()
    _checkpointer.cache_clear()


def is_cold_thread(thread_id: str) -> bool:
    """Whether this thread_id has no prior conversation state.

    True for a thread_id that has never been invoked (or a fresh process).
    Used by the pipeline to decide whether a follow-up can rely on memory of
    a prior traversal or needs to stand on its own.
    """
    agent = build_orchestrator()
    config = {"configurable": {"thread_id": thread_id}}
    return not agent.get_state(config).values


def run_decision_tree(input_content: str, *, thread_id: str) -> str:
    """Walk (or continue) the decision tree on a given conversation thread.

    :param input_content: the new message to send - either the initial
        filter text + decision tree JSON (ORCHESTRATOR_INPUT_TEMPLATE), or a
        bare follow-up message on an existing thread.
    :param thread_id: identifies the conversation. Re-invoking with the same
        thread_id resumes from that conversation's full prior history; a new
        thread_id starts fresh. The API layer passes the session_id here.
    :return: the trace produced by THIS turn only (prior turns' trace text is
        excluded, even though the underlying conversation history includes
        them).
    """
    agent = build_orchestrator()
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": AGENT_RECURSION_LIMIT,
    }

    # Once a checkpointer is attached, result["messages"] on a continued
    # thread contains the ENTIRE accumulated history, not just this turn's
    # new messages. Capture the prior length so only the new tail gets
    # trace-formatted below - otherwise every follow-up would re-include
    # every earlier turn's trace text.
    prior_state = agent.get_state(config)
    prior_count = len(prior_state.values.get("messages", [])) if prior_state.values else 0

    result = agent.invoke(
        input={"messages": [{"role": "user", "content": input_content}]},
        config=config,
    )

    if not result or not result.get("messages"):
        raise OrchestrationError("The orchestrator agent returned no messages.")

    new_messages = result["messages"][prior_count:]
    agent_messages = filter_messages(
        new_messages,
        include_names=(ORCHESTRATOR_AGENT_NAME,),
        exclude_tool_calls=False,
    )

    trace = "\n".join(
        text for message in agent_messages if (text := message_text(message.content))
    )
    logger.info("Decision tree traversal produced %d characters of trace", len(trace))
    return trace
