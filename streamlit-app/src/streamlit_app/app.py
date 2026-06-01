from __future__ import annotations

import streamlit as st
from streamlit_app.auth.session import ensure_valid_token, handle_auth_callback, logout
from streamlit_app.ui.assistant import render_assistant
from streamlit_app.ui.login import render_login


def main() -> None:
    st.set_page_config(
        page_title="Acme Operations Agent",
        layout="centered",
    )

    st.title("Acme Operations Agent")

    if "access_token" not in st.session_state:
        if handle_auth_callback():
            return

        render_login()
        return

    if not ensure_valid_token():
        st.error("Your session has expired. Please sign in again.")
        logout()
        return

    render_assistant()


if __name__ == "__main__":
    main()
