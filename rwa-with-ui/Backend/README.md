# RWA Explainability — Backend

Agentic explainability for Risk Weighted Asset calculations. An analyst pastes a
clarification email about an already-computed transaction/counterparty; the
agents walk a scenario decision tree, fetching the value of one field at each
step, and return both the stopping conclusion and a full trace of how they got
there.

---

## Quick start

```bash
cd Backend && ./scripts/setup.sh
```

Then put your key in `Backend/.env`:

```
OPENAI_API_KEY=sk-...
```

Verify the model and thinking level are accepted before serving traffic:

```bash
./.venv/bin/python -m app.llm.check
```

Start the API:

```bash
./scripts/run_api.sh
```

`http://localhost:8000/health` → `{"status":"ok"}`.
`http://localhost:8000/docs` → interactive API docs.
`http://localhost:8000/api/rwa/config` → the LLM settings actually in effect.

---

## Folder layout

```
Backend/
├── config/
│   └── llm.yaml                 ← model + thinking level. Edit this.
├── app/
│   ├── main.py                  FastAPI entry point
│   ├── settings.py              paths, CORS, limits (all env-overridable)
│   │
│   ├── agents/                  ← THE AGENTS
│   │   ├── classifier.py            email → issue type
│   │   ├── orchestrator.py          walks the decision tree
│   │   ├── conclusion.py            trace → 2-3 sentence summary
│   │   ├── pipeline.py              wires them into the two API flows
│   │   └── table_agents/        ← one data agent per source table
│   │       ├── base.py              shared pandas-agent construction
│   │       ├── mart.py              OM_CDM_RWA_MTRC
│   │       └── mart_extn.py         OM_CDM_RWA_MTRC_EXTN
│   │
│   ├── tools/                   ← TOOLS THE AGENTS CALL
│   │   ├── check_steps.py           fetch step N from the decision tree
│   │   └── table_prompt.py          fetch a table's extraction prompt
│   │
│   ├── prompts/                 every prompt, one module per agent family
│   ├── llm/                     config loader, client factory, checker
│   ├── data/                    Excel loaders (tables + decision trees)
│   └── api/                     routes, schemas, session store
│
├── data/
│   └── Main Data.xlsx           the mock source tables (6 sheets)
│
├── docs/                        ← DOCUMENTS
│   ├── decision-trees/
│   │   └── Issue Types and Steps.xlsx   the scenario trees (read at runtime)
│   ├── sample-emails/           example inbound emails (not read by code)
│   └── reference-data/          sample JSON payloads (not read by code)
│
├── legacy/                      superseded code, not part of the app
└── scripts/                     setup.sh, run_api.sh
```

---

## How a request flows

```
POST /api/rwa/email-submit
        │
        ▼
  classifier            one LLM call → "Collateral Market Value drop ..."
        │
        ▼
  pipeline              looks up that issue type's tree in
                        docs/decision-trees/Issue Types and Steps.xlsx
        │
        ▼
  orchestrator ────────────────────────────────────┐  loops until a
        │  get_check_step_to_process("3.1")        │  stopping criterion
        │  get_prompt_using_table_name("mart_extn")│  is reached, or
        │  mart_extn_tool → runs a pandas query    │  recursion_limit hits
        │  judge Pass/Fail, pick the next step ────┘
        ▼
  conclusion            trace → summary shown as the UI header
```

Step selection, branching and the stopping criterion are decided by the model
from prompt text — there is no coded state machine. `RWA_AGENT_RECURSION_LIMIT`
(default 100) is the only hard stop.

---

## Changing the model or the thinking level

Everything is in [`config/llm.yaml`](config/llm.yaml). Change one line to switch
the model for the whole app:

```yaml
defaults:
  model: gpt-5.6-terra
  reasoning:
    effort: medium        # none | minimal | low | medium | high
```

Per-agent overrides live under `roles:` — give the orchestrator a bigger
thinking budget than the table agents, for example:

```yaml
roles:
  orchestrator:
    reasoning:
      effort: high
  table_agent:
    reasoning:
      effort: minimal
```

Values left `null` are never sent to the API, so the model's own default
applies. This matters for `temperature`: reasoning models reject it. If you
switch to a classic chat model such as `gpt-4o`, set `temperature: 0`.

Restart the API after editing — the config is read once per process.

---

## Where the data comes from

Local Excel only. No database, no external API.

| Table (sheet in `data/Main Data.xlsx`) | Has an agent? |
|---|---|
| `om_cdm_rwa_mtrc` | yes — `mart_tool` |
| `om_cdm_rwa_mtrc_extn` | yes — `mart_extn_tool` |
| `dsft_conc_txn_result` | no |
| `dsft_conc_result_txn_map` | no |
| `dsft_conc_result` | no |
| `dsft_fi_base_subassetclass` | no |

The four without agents are loaded but unreachable: they have neither an
extraction prompt nor a registered agent. To add one, see the checklist in
`app/agents/table_agents/__init__.py`.

Only one issue type currently has a decision tree defined
(`Collateral Market Value drop observed for Inbound trades`). The other three
the classifier can emit return "Issue type is not supported yet." Add a row to
`docs/decision-trees/Issue Types and Steps.xlsx` to support one — no code change
needed.

---

## Environment variables

All optional except the key. See [`.env.example`](.env.example).

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required.** |
| `CORS_ORIGINS` | `http://localhost:4200` | Comma-separated allowed origins. |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8000` | Bind address. |
| `LANGSMITH_API_KEY` | — | Enables tracing when set. |
| `RWA_SOURCE_TABLES_FILE` | `data/Main Data.xlsx` | Source tables workbook. |
| `RWA_DECISION_TREE_FILE` | `docs/decision-trees/…xlsx` | Decision trees workbook. |
| `RWA_LLM_CONFIG_FILE` | `config/llm.yaml` | LLM config location. |
| `RWA_AGENT_RECURSION_LIMIT` | `100` | Hard stop on the agent loop. |

Paths are resolved relative to `Backend/`, so the app runs identically from any
working directory.
