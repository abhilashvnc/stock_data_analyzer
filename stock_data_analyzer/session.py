import streamlit as st
from providers import PROVIDER_REGISTRY
from data import DATA_SOURCE_REGISTRY


def init_session() -> None:
    if "provider_sessions" not in st.session_state:
        st.session_state.provider_sessions = {
            name: {
                "provider": provider,  # the actual BaseProvider instance
                "show_auth": True,
                "model_list": [],
                "selected_model": None,
            }
            for name, provider in PROVIDER_REGISTRY.items()
        }

    if "active_provider" not in st.session_state:
        st.session_state.active_provider = list(PROVIDER_REGISTRY.keys())[0]

    if "active_data_source" not in st.session_state:
        st.session_state.active_data_source = "yfinance"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_key" not in st.session_state:
        st.session_state.chat_key = ""

    if "ls_loaded" not in st.session_state:
        st.session_state.ls_loaded = False


def get_active_provider():
    name = st.session_state.active_provider
    return st.session_state.provider_sessions[name]["provider"]


def get_active_data_source():
    name = st.session_state.active_data_source
    return DATA_SOURCE_REGISTRY[name]
