import json
import streamlit as st
import streamlit.components.v1 as components
from providers import PROVIDER_REGISTRY

LS_KEY = "stock_analyst_sessions"


def localstorage_save() -> None:
    """Serialise all authenticated providers to localStorage."""
    saveable = {}
    for name, sess in st.session_state.provider_sessions.items():
        provider = sess["provider"]
        if provider.is_authenticated:
            saveable[name] = {
                "credentials": provider.dump_credentials(),
            }

    payload = json.dumps(saveable).replace("`", "\\`")
    components.html(
        f"""
        <script>
            localStorage.setItem('{LS_KEY}', `{payload}`);
        </script>
    """,
        height=0,
    )


def localstorage_clear() -> None:
    """Wipe localStorage entry."""
    components.html(
        f"""
        <script>
            localStorage.removeItem('{LS_KEY}');
        </script>
    """,
        height=0,
    )


def localstorage_load_component() -> None:
    """
    Inject JS that reads localStorage and passes it back via query params.
    Only runs once — guarded by ls_loaded flag.
    """
    if st.session_state.ls_loaded:
        return

    components.html(
        f"""
        <script>
            const data = localStorage.getItem('{LS_KEY}');
            if (data) {{
                const encoded = encodeURIComponent(data);
                const url = new URL(window.parent.location.href);
                url.searchParams.set('_ls_creds', encoded);
                window.parent.history.replaceState({{}}, '', url.toString());
                window.parent.location.reload();
            }}
        </script>
    """,
        height=0,
    )


def restore_from_query_params() -> None:
    """
    On page load, if _ls_creds is in query params,
    restore and re-authenticate each provider silently.
    """
    if st.session_state.ls_loaded:
        return

    raw = st.query_params.get("_ls_creds", None)
    if not raw:
        st.session_state.ls_loaded = True
        return

    try:
        saved = json.loads(raw)
        for name, data in saved.items():
            if name not in st.session_state.provider_sessions:
                continue

            sess = st.session_state.provider_sessions[name]
            provider = sess["provider"]
            result = provider.load_credentials(data["credentials"])

            if result.success:
                sess["show_auth"] = False
                sess["model_list"] = provider.list_models()
    except Exception:
        pass

    st.query_params.clear()
    st.session_state.ls_loaded = True
