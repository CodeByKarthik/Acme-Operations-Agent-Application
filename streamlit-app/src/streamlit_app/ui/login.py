from __future__ import annotations

import streamlit as st
from streamlit_app.auth.session import get_auth_url


def render_login() -> None:
    st.subheader("Sign in required")
    st.write("Use your Acme Operations account to continue.")

    st.markdown(
        f"<a href='{get_auth_url()}' target='_self'>Login with Keycloak</a>",
        unsafe_allow_html=True,
    )