from __future__ import annotations

import uuid
from typing import Any

import requests
import streamlit as st

from streamlit_app.auth.session import ensure_valid_token
from streamlit_app.config import settings  # type: ignore[import-untyped]


API_BASE_URL = settings.api_base_url


def _get_conversation_id() -> str:
    """
    Return a stable conversation ID for the current session.
    """
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = str(uuid.uuid4())
    return st.session_state["conversation_id"]


def call_agent_api(message: str) -> str:
    if not ensure_valid_token():
        return "Your session has expired. Please sign in again."

    token = st.session_state["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "message": message,
        "conversation_id": _get_conversation_id(),
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException:
        return "I could not reach the assistant service. Please try again."

    if response.status_code == 401:
        return "Your session is no longer valid. Please sign in again."

    if response.status_code == 403:
        return "You do not have permission to perform this action."

    if response.status_code != 200:
        return "The assistant could not process this request. Please try again."

    try:
        data: dict[str, Any] = response.json()
    except ValueError:
        return "The assistant returned an unreadable response."

    return str(data.get("answer") or "No answer was returned.")