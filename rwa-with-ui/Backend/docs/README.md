# docs/

| Folder | Read by the app? | Contents |
|---|---|---|
| `decision-trees/` | **Yes, at runtime** | `Issue Types and Steps.xlsx` — one row per issue type; the `Check Steps` cell holds the tree as JSON. This is the file to edit to change what the agents check. |
| `sample-emails/` | No | Example inbound analyst emails. Paste one into the UI to try the app. |
| `reference-data/` | No | Sample JSON payloads showing the shape of each source table, plus an older copy of the data workbook. Reference material only. |

## Editing a decision tree

`decision-trees/Issue Types and Steps.xlsx` has two columns:

| Issue Type | Check Steps |
|---|---|
| `Collateral Market Value drop observed for Inbound trades` | `{"1": "...", "2": "...", "3": "...", "3.1": "...", ...}` |

Rules the orchestrator relies on:

- **Keys encode the tree shape.** `"3"` is a main step; `"3.1"`–`"3.5"` are its
  sub-steps. Sub-steps are processed in order before the next main step.
- **Branching is written in English inside each step.** For example:
  *"If condition is TRUE then directly move to Step 4 or else go to sub steps."*
  The agent reads that sentence and decides where to go — there is no separate
  routing table.
- **Stopping criteria are the "reply to user that …" clauses**, plus a final
  step that declares the analysis inconclusive.
- **Name the table** in the step text (`in Mart Extn table`) when the field is
  not on `om_cdm_rwa_mtrc`, which is the default.

Adding a new row here is enough to support a new issue type — no code change —
as long as the classifier can emit that exact issue-type string (see
`app/prompts/classification.py`) and every table the steps reference has a
registered agent (see `app/agents/table_agents/__init__.py`).

The app re-reads these workbooks only at startup; restart the API after editing.
