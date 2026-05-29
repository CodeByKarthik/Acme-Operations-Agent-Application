from __future__ import annotations

import streamlit as st

from streamlit_app.auth.session import get_logged_in_user, logout
from streamlit_app.client.api_client import call_agent_api


def render_assistant() -> None:
    st.caption(f"Signed in as {get_logged_in_user()}")

    if st.button("Logout"):
        logout()

    st.divider()

    question = st.text_area(
        "Your question",
        height=120,
        placeholder=(
            "Example: Show me open customer issues for Globex Corporation, "
            "summarise the latest status, and suggest the next action."
        ),
    )

    if st.button("Send", type="primary"):
        question = question.strip()

        if not question:
            st.warning("Enter a question first.")
            return

        with st.spinner("Working on your request..."):
            answer = call_agent_api(question)

        st.session_state["last_question"] = question
        st.session_state["last_answer"] = answer

    if "last_answer" in st.session_state:
        st.subheader("Assistant")

        last_question = st.session_state.get("last_question")
        if isinstance(last_question, str):
            st.caption(f"Question: {last_question}")

        st.write(st.session_state["last_answer"])