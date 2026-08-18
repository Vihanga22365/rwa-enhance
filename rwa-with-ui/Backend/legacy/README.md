# legacy/

Not part of the running application.

| File | What it is |
|---|---|
| `streamlit_app.py` | The original Streamlit UI, superseded by the Angular frontend. Updated to import from `app/`, so it still works. Streamlit is not in `requirements.txt` — `pip install streamlit` first. |
| `unrelated_chatbot_prompts.py` | Prompt drafts for an unrelated banking-accessibility chatbot. Nothing in this project imports it. Safe to delete. |

The pre-refactor monolith (`graph.py`, `tools.py`, `prompt.py`, `webapp_api.py`,
`test_graph.py`) was removed rather than copied here — it is in git history if
you need it:

```bash
git show HEAD:Backend/graph.py
```
