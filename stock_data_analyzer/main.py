import streamlit as st
from session import init_session, get_active_provider, get_active_data_source
from ui.storage import localstorage_load_component, restore_from_query_params
from ui.sidebar import render_sidebar
from ui.chat import render_chat

st.set_page_config(page_title="AI Stock Analyst", page_icon="📈")

init_session()
restore_from_query_params()

if not st.session_state.ls_loaded:
    localstorage_load_component()
    st.stop()

st.title("📈 AI Stock Analyst")

render_sidebar()

provider = get_active_provider()
if not provider.is_authenticated:
    st.info("👈 Connect to a provider in the sidebar to get started.")
    st.stop()

render_chat(provider, get_active_data_source())
