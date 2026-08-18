"""Legacy Streamlit UI - superseded by the Angular frontend.

Kept because it is a fast way to exercise the agents without running the SPA.
Streamlit is NOT in requirements.txt; install it separately to use this:

    pip install streamlit
    streamlit run legacy/streamlit_app.py --server.port 8184

Run it from the Backend/ directory so `app` is importable.
"""

import sys
from pathlib import Path

import streamlit as st

# Allow running via `streamlit run legacy/streamlit_app.py` from Backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents import (  # noqa: E402
    classify_issue_type,
    generate_final_conclusion,
    run_follow_up,
    run_initial_analysis,
)


def on_submit_button_clicked():
    """Callback function for the submit button."""
    with st.spinner("Agents are processing..."):
        issue_type = classify_issue_type(input_text)
        st.session_state.issue_type = issue_type
        st.session_state.messages.append(
            {"role": "assistant", "content": f"###### Classified Issue Type: {issue_type}"}
        )
        agent_response = run_initial_analysis(issue_type, input_text)
        final_conclusion = generate_final_conclusion(input_text, agent_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response, "label": final_conclusion}
        )


if "messages" not in st.session_state:
    st.session_state.messages = []
if "issue_type" not in st.session_state:
    st.session_state.issue_type = ""

st.set_page_config(layout="centered", page_title="RWA Model Explainability")
st.sidebar.markdown("# RWA Model Explainability ")

st.markdown(
    """
<style>
div[data-testid="stMarkdownContainer"] {
    font-size: 16px;
    font-weight: 600;
}
div[data-testid="stMarkdownContainer"] p {
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True,
)

input_text = st.sidebar.text_area("Insert Email Subject and Content", height=350)

col1, col2 = st.sidebar.columns([2, 1])
with col2:
    if input_text:
        st.button(
            "Submit", type="primary", on_click=on_submit_button_clicked, use_container_width=True
        )

for message in st.session_state.messages:
    session_msg = st.chat_message(message["role"])
    if "label" in message:
        session_msg.expander(message["label"]).write(message["content"])
    else:
        session_msg.write(message["content"])

if user_chat_input := st.chat_input("Ask a follow-up question..."):
    st.chat_message("user").write(user_chat_input)
    st.session_state.messages.append({"role": "user", "content": user_chat_input})
    with st.spinner("Agents are processing..."):
        agent_response = run_follow_up(input_text, user_chat_input)
        final_conclusion = generate_final_conclusion(input_text, agent_response)
        st.chat_message("assistant").expander(final_conclusion).write(agent_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response, "label": final_conclusion}
        )
