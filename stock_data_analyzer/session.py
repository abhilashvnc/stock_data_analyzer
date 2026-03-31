import streamlit as st
from providers import PROVIDER_REGISTRY
from data import DATA_SOURCE_REGISTRY


def init_session() -> None:
    if "provider_sessions" not in st.session_state:
        st.session_state.provider_sessions = {
            name: {
                "provider": provider,
                "show_auth": True,
                "model_list": [],
                "selected_model": None,
            }
            for name, provider in PROVIDER_REGISTRY.items()
        }

    if "active_provider" not in st.session_state:
        st.session_state.active_provider = list(PROVIDER_REGISTRY.keys())[0]

    # Set of active data source names — all on by default
    if "active_data_sources" not in st.session_state:
        st.session_state.active_data_sources = set(DATA_SOURCE_REGISTRY.keys())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_key" not in st.session_state:
        st.session_state.chat_key = ""

    if "fetch_key" not in st.session_state:
        st.session_state.fetch_key = ""

    if "stock_ctx" not in st.session_state:
        st.session_state.stock_ctx = None

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = ""

    if "ls_loaded" not in st.session_state:
        st.session_state.ls_loaded = False


def get_active_provider():
    name = st.session_state.active_provider
    return st.session_state.provider_sessions[name]["provider"]


def get_active_data_sources() -> list:
    """Returns list of active BaseDataSource instances."""
    from data import DATA_SOURCE_REGISTRY

    return [
        DATA_SOURCE_REGISTRY[name]
        for name in st.session_state.active_data_sources
        if name in DATA_SOURCE_REGISTRY
    ]
