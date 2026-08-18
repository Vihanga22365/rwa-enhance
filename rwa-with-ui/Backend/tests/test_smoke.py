"""Smoke tests for the parts of the refactor that need no API key.

Run from Backend/:
    ./.venv/bin/python -m pytest tests -q
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.agents.classifier import NO_ISSUE_MATCHED, classify_issue_type
from app.agents.pipeline import UNSUPPORTED_ISSUE_MESSAGE, run_initial_analysis
from app.agents.table_agents import REGISTERED_SPECS
from app.data import TABLE_NAMES, get_check_steps, list_issue_types, load_tables
from app.llm import KNOWN_ROLES, get_llm_settings
from app.llm.factory import build_client_kwargs
from app.llm.messages import message_text
from app.main import app
from app.prompts.classification import ISSUE_CLASSIFICATION_PROMPT
from app.prompts.orchestrator import ORCHESTRATOR_PROMPT
from app.prompts.table_agents import PANDAS_AGENT_PROMPT_MART, PANDAS_AGENT_PROMPT_MART_EXTN
from app.tools import get_check_step_to_process, get_prompt_using_table_name

client = TestClient(app)


# --- data ---------------------------------------------------------------


def test_every_source_table_loads():
    tables = load_tables()
    assert set(tables) == set(TABLE_NAMES)
    for name in TABLE_NAMES:
        assert not tables[name].empty, f"{name} is empty"


def test_decision_tree_is_valid_json_with_expected_steps():
    # Structural only, deliberately not coupled to any one workbook's content -
    # this must keep passing across a "swap the workbook" data change.
    issue_types = list_issue_types()
    assert issue_types, "no decision trees defined"

    for issue_type in issue_types:
        steps = json.loads(get_check_steps(issue_type))
        assert steps, f"{issue_type} has no steps"
        assert "1" in steps, f"{issue_type} has no step 1"
        assert all(isinstance(v, str) and v.strip() for v in steps.values())


# --- tools --------------------------------------------------------------


def test_check_step_lookup_returns_step_text():
    steps = json.dumps({"1": "first", "3.1": "a sub step"})
    assert get_check_step_to_process("1", steps) == "first"
    assert get_check_step_to_process("3.1", steps) == "a sub step"


def test_check_step_lookup_explains_a_missing_step():
    result = get_check_step_to_process("99", json.dumps({"1": "first"}))
    assert "No step" in result and "Available steps" in result


def test_check_step_lookup_rejects_malformed_json():
    with pytest.raises(ValueError):
        get_check_step_to_process("1", "not json")


def test_table_prompt_is_filled_in_for_wired_tables():
    prompt = get_prompt_using_table_name(
        "om_cdm_rwa_mtrc", "GFCID '1123456918'", "Extract LGL_CERTAINTY_FLG"
    )
    assert "1123456918" in prompt
    assert "LGL_CERTAINTY_FLG" in prompt

    extn = get_prompt_using_table_name(
        "om_cdm_rwa_mtrc_extn", "GFCID '1123456918'", "Extract lrm_flg"
    )
    assert "principal_gfcid" in extn


def test_table_prompt_is_none_for_tables_without_one():
    assert get_prompt_using_table_name("dsft_conc_result", "x", "y") is None
    assert get_prompt_using_table_name("no_such_table", "x", "y") is None


# --- agents -------------------------------------------------------------


def test_registered_table_agents_point_at_real_sheets():
    for spec in REGISTERED_SPECS:
        assert spec.table_name in TABLE_NAMES
        assert spec.schema_prompt, f"{spec.tool_name} has no schema prompt"


def test_unsupported_issue_type_short_circuits_before_any_llm_call():
    # No API key needed: this must return before the orchestrator is built.
    # Deliberately not a real category from any workbook - this must fail the
    # list_issue_types() membership check regardless of which workbook is loaded.
    assert (
        run_initial_analysis(
            "Some Made Up Issue Type Not In The Workbook", "some email", thread_id="test-thread"
        )
        == UNSUPPORTED_ISSUE_MESSAGE
    )


def test_message_text_flattens_reasoning_model_content_blocks():
    # Every agent (classifier, orchestrator, conclusion) reads .content through
    # this helper, because /v1/responses models return blocks, not a string.
    assert message_text("plain") == "plain"
    assert message_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]) == "a\nb"
    # Reasoning blocks carry no "text" and must not crash or leak.
    assert message_text([{"type": "reasoning", "summary": []}]) == ""
    assert message_text(None) == ""


# --- classification -------------------------------------------------------


def test_classification_prompt_includes_current_workbook_issue_types():
    # The prompt is built at call time from list_issue_types(), not hardcoded -
    # this is what makes classification survive a workbook swap.
    issue_types = list_issue_types()
    prompt = ISSUE_CLASSIFICATION_PROMPT.format(
        issue_type_list="\n".join(f"{i}. {t}" for i, t in enumerate(issue_types, 1)),
        input_text="dummy",
    )
    for issue_type in issue_types:
        assert issue_type in prompt

    # No leftover hardcoded old-category strings baked into the template itself.
    assert "PSE/EAD differences" not in ISSUE_CLASSIFICATION_PROMPT
    assert "Clarifications related to Concentration" not in ISSUE_CLASSIFICATION_PROMPT


def test_classify_issue_type_returns_no_match_when_no_trees_defined(monkeypatch):
    monkeypatch.setattr("app.agents.classifier.list_issue_types", lambda: [])
    # No LLM call should be attempted - if get_llm were reached with no valid API
    # key, this would raise instead of returning cleanly.
    assert classify_issue_type("anything") == NO_ISSUE_MATCHED


# --- memory / checkpointer -----------------------------------------------


def test_checkpointer_isolates_and_continues_threads():
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.prebuilt import create_react_agent

    fake_model = FakeMessagesListChatModel(
        responses=[AIMessage(content="ok-1"), AIMessage(content="ok-2")]
    )
    agent = create_react_agent(model=fake_model, tools=[], checkpointer=InMemorySaver())

    cfg_a = {"configurable": {"thread_id": "thread-a"}}
    cfg_b = {"configurable": {"thread_id": "thread-b"}}

    # A never-used thread has empty state - this is the exact mechanism
    # is_cold_thread() relies on in app/agents/orchestrator.py.
    assert not agent.get_state(cfg_a).values
    assert not agent.get_state(cfg_b).values

    agent.invoke({"messages": [{"role": "user", "content": "hello"}]}, config=cfg_a)
    state_a = agent.get_state(cfg_a)
    assert len(state_a.values["messages"]) > 0

    # thread-b is untouched by thread-a's turn.
    assert not agent.get_state(cfg_b).values

    # Continuing thread-a builds on its prior history rather than starting fresh.
    prior_len = len(state_a.values["messages"])
    agent.invoke({"messages": [{"role": "user", "content": "follow up"}]}, config=cfg_a)
    assert len(agent.get_state(cfg_a).values["messages"]) > prior_len


# --- orchestrator / table prompts ------------------------------------------


def test_softened_table_prompts_still_describe_sensible_defaults():
    for prompt in (PANDAS_AGENT_PROMPT_MART, PANDAS_AGENT_PROMPT_MART_EXTN):
        assert "15" in prompt and "16" in prompt  # default BAL_TYP_CD still documented
        assert "does not specify" in prompt  # conditional carve-out language present
    assert "'B'" in PANDAS_AGENT_PROMPT_MART  # default BUY_SELL_IND still documented


def test_orchestrator_prompt_only_lists_wired_tables():
    for unwired in (
        "dsft_conc_txn_result",
        "dsft_conc_result_txn_map",
        "dsft_conc_result",
        "dsft_fi_base_subassetclass",
    ):
        assert unwired not in ORCHESTRATOR_PROMPT
    assert "om_cdm_rwa_mtrc" in ORCHESTRATOR_PROMPT
    assert "om_cdm_rwa_mtrc_extn" in ORCHESTRATOR_PROMPT


def test_orchestrator_prompt_has_simulation_carveout_and_mode_labels():
    assert "HYPOTHETICAL" in ORCHESTRATOR_PROMPT
    assert "HUMAN-DIRECTED" in ORCHESTRATOR_PROMPT
    assert "AD HOC FOLLOW-UP" in ORCHESTRATOR_PROMPT
    assert "MODE:" in ORCHESTRATOR_PROMPT
    # The old unconditional ban is gone / replaced by a conditional rule.
    assert "UNLESS the current user message explicitly requests" in ORCHESTRATOR_PROMPT


# --- config -------------------------------------------------------------


def test_each_role_resolves_and_inherits_the_default_model():
    settings = {role: get_llm_settings(role) for role in KNOWN_ROLES}
    models = {s.model for s in settings.values()}
    assert len(models) == 1, "roles should inherit one default model unless overridden"
    assert settings["orchestrator"].reasoning_effort == "medium"
    assert settings["table_agent"].reasoning_effort == "low"


def test_null_config_values_are_never_sent_to_the_api():
    kwargs = build_client_kwargs(get_llm_settings("orchestrator"))
    # temperature is null in llm.yaml because reasoning models reject it.
    assert "temperature" not in kwargs
    assert "max_tokens" not in kwargs
    assert kwargs["model"]


def test_responses_api_is_used_for_tool_calling_agents():
    # gpt-5.6-terra 400s on /v1/chat/completions when reasoning_effort is set
    # together with function tools ("use /v1/responses or set reasoning_effort
    # to 'none'"). The orchestrator and table agents both call tools, so they
    # must route through the responses API.
    for role in ("orchestrator", "table_agent"):
        kwargs = build_client_kwargs(get_llm_settings(role))
        assert kwargs.get("use_responses_api") is True, role


# --- api ----------------------------------------------------------------


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_endpoint_reports_live_settings():
    body = client.get("/api/rwa/config").json()
    assert set(body["llm"]) == set(KNOWN_ROLES)
    assert body["issue_types_with_decision_trees"] == list_issue_types()


def test_empty_payloads_are_rejected():
    assert client.post("/api/rwa/email-submit", json={"input_text": ""}).status_code == 422
    assert client.post("/api/rwa/follow-up", json={"user_chat_input": ""}).status_code == 422
