"""Read application settings from local environment or Streamlit secrets."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


def get_setting(name: str, default: str | None = None) -> str | None:
    """Return a setting from environment variables or hosted Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        # Streamlit secrets are unavailable during local non-Streamlit runs.
        value = None
    return value or default
