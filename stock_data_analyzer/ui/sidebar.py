import streamlit as st
from providers import PROVIDER_REGISTRY, ProviderBasicAuth, ProviderAPIKeyAuth
from providers.base import AuthResult
from data import DATA_SOURCE_REGISTRY
from ui.storage import localstorage_save


# ==============================
# TOP LEVEL
# ==============================
def render_sidebar() -> None:
    with st.sidebar:
        st.header("🤖 Model Settings")
        _render_provider_selector()
        st.divider()
        _render_data_source_selector()


# ==============================
# PROVIDER SELECTOR
# ==============================
def _render_provider_selector() -> None:
    provider_names = list(PROVIDER_REGISTRY.keys())

    active = st.selectbox(
        "Provider",
        provider_names,
        key="provider_select",
    )
    st.session_state.active_provider = active

    sess = st.session_state.provider_sessions[active]
    provider = sess["provider"]

    if not provider.is_authenticated or sess["show_auth"]:
        _render_auth_form(active)
    else:
        _render_model_section(active)


# ==============================
# AUTH FORM
# ==============================
def _render_auth_form(provider_name: str) -> None:
    sess = st.session_state.provider_sessions[provider_name]
    provider = sess["provider"]

    # If already authenticated but showing auth (credential change),
    # show a cancel button so the user can go back without logging out
    if provider.is_authenticated and sess["show_auth"]:
        if st.sidebar.button(
            "✕ Cancel",
            key=f"cancel_auth_{provider_name}",
            use_container_width=True,
        ):
            sess["show_auth"] = False
            st.rerun()

    st.sidebar.markdown(f"**Connect to {provider_name}**")

    # Build form fields based on AUTH_TYPE
    auth_type = provider.AUTH_TYPE

    with st.sidebar.form(key=f"auth_form_{provider_name}"):
        creds: dict = {}

        if auth_type == ProviderBasicAuth:
            existing = provider.provider_auth

            creds["host"] = st.text_input(
                "Host URL",
                value=existing.host if existing else "http://localhost:11434",
            )
            creds["username"] = st.text_input(
                "Username",
                value=existing.username if existing else "",
            )
            creds["password"] = st.text_input(
                "Password",
                value=existing.password if existing else "",
                type="password",
            )

        elif auth_type == ProviderAPIKeyAuth:
            existing = provider.provider_auth

            creds["api_key"] = st.text_input(
                "API Key",
                value=existing.api_key if existing else "",
                type="password",
            )
            # Show host field only if provider supports custom host
            if hasattr(existing, "host") and existing is not None:
                creds["host"] = st.text_input(
                    "Host (optional)",
                    value=existing.host or "",
                )

        connect_clicked = st.form_submit_button("🔌 Connect", use_container_width=True)

    if connect_clicked:
        _handle_connect(provider_name, creds)


def _handle_connect(provider_name: str, creds: dict) -> None:
    sess = st.session_state.provider_sessions[provider_name]
    provider = sess["provider"]
    auth_type = provider.AUTH_TYPE

    with st.sidebar.status(f"Connecting to {provider_name}..."):
        try:
            auth_obj = auth_type(**creds)
        except TypeError as e:
            st.sidebar.error(f"❌ Invalid credentials: {e}")
            return

        result: AuthResult = provider.authenticate(auth_obj)

    if not result.success:
        st.sidebar.error(f"❌ {result.error}")
        return

    # Auth succeeded — update UI state
    sess["show_auth"] = False
    sess["model_list"] = provider.list_models()
    localstorage_save()
    st.rerun()


# ==============================
# MODEL SECTION
# ==============================
def _render_model_section(provider_name: str) -> None:
    sess = st.session_state.provider_sessions[provider_name]
    provider = sess["provider"]

    # Connected status row
    col_status, col_key = st.sidebar.columns([3, 1])
    col_status.success("✅ Connected")
    if col_key.button(
        "🔑", help="Change credentials", key=f"change_creds_{provider_name}"
    ):
        sess["show_auth"] = True
        st.rerun()

    # Logout
    if st.sidebar.button(
        "🚪 Logout",
        key=f"logout_{provider_name}",
        use_container_width=True,
    ):
        _handle_logout(provider_name)

    st.sidebar.divider()

    # Model dropdown + refresh on same row
    model_list = sess.get("model_list", [])

    col_model, col_refresh = st.sidebar.columns([4, 1])

    with col_model:
        if model_list:
            previous = sess.get("selected_model")
            default_idx = model_list.index(previous) if previous in model_list else 0
            chosen = st.selectbox(
                "Model",
                model_list,
                index=default_idx,
                key=f"model_select_{provider_name}",
            )
            sess["selected_model"] = chosen
        else:
            st.warning("No models found.")
            sess["selected_model"] = None

    with col_refresh:
        # Nudge button down to align with selectbox
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄", help="Refresh model list", key=f"refresh_{provider_name}"):
            with st.sidebar.status("Fetching models..."):
                sess["model_list"] = provider.list_models()
            st.rerun()


def _handle_logout(provider_name: str) -> None:
    sess = st.session_state.provider_sessions[provider_name]
    provider = sess["provider"]

    provider.logout()
    sess["show_auth"] = True
    sess["model_list"] = []
    sess["selected_model"] = None
    localstorage_save()
    st.rerun()


# ==============================
# DATA SOURCE SELECTOR
# ==============================
def _render_data_source_selector() -> None:
    from data import DATA_SOURCE_REGISTRY

    source_names = list(DATA_SOURCE_REGISTRY.keys())

    # Nothing to configure if only one source exists
    if len(source_names) == 1:
        st.sidebar.caption(f"📊 Data: {source_names[0]}")
        st.session_state.active_data_sources = {source_names[0]}
        return

    st.sidebar.markdown("**📊 Data Sources**")

    active: set = st.session_state.active_data_sources
    new_active: set = set()

    for name in source_names:
        is_on = name in active

        # If this is the last active source, disable its toggle
        # so the user cannot turn it off
        is_last_active = is_on and len(active) == 1
        toggled = st.sidebar.toggle(
            name,
            value=is_on,
            key=f"ds_toggle_{name}",
            disabled=is_last_active,
            help=(
                "At least one data source must remain active."
                if is_last_active
                else None
            ),
        )
        if toggled:
            new_active.add(name)

    # Safety net — should never be empty due to disabled toggle, but guard anyway
    if not new_active:
        new_active = {source_names[0]}

    st.session_state.active_data_sources = new_active
