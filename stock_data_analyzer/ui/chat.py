import streamlit as st
from providers.base import BaseProvider
from data.base import BaseDataSource, StockContext
import hashlib


# ==============================
# MAIN ENTRY
# ==============================
def render_chat(provider: BaseProvider, data_source: BaseDataSource) -> None:
    sess = st.session_state.provider_sessions[st.session_state.active_provider]
    selected_model = sess.get("selected_model")

    ticker_input = st.text_input(
        "Enter Stock Ticker (e.g. RELIANCE, TCS, INFY)",
        key="ticker_input",
    )

    if not ticker_input:
        return

    ticker = _normalise_ticker(ticker_input)

    # Cache key based on ticker + data source only — not provider or model
    fetch_key = f"{ticker}__{data_source.source_name}"

    # Only fetch when ticker or data source changes
    if st.session_state.get("fetch_key") != fetch_key:
        with st.spinner("Fetching stock data..."):
            fetch_result = data_source.fetch(ticker)

        if not fetch_result.success or fetch_result.context is None:
            st.error(f"❌ {fetch_result.error}")
            return

        st.session_state.fetch_key = fetch_key
        st.session_state.stock_ctx = fetch_result.context
        st.session_state.system_prompt = data_source.build_prompt(fetch_result.context)

        # New ticker = new chat
        st.session_state.messages = [
            {"role": "system", "content": st.session_state.system_prompt}
        ]

    ctx = st.session_state.get("stock_ctx")
    if ctx is None:
        return

    _render_metrics(ctx)

    if not selected_model:
        st.warning("⚠️ No model selected. Refresh the model list in the sidebar.")
        return

    # Changing provider or model does NOT reset chat anymore
    _render_messages()
    _handle_input(provider, selected_model)


# ==============================
# HELPERS
# ==============================
def _normalise_ticker(raw: str) -> str:
    ticker = raw.upper().strip()
    if not ticker.endswith(".NS"):
        ticker += ".NS"
    return ticker


def _render_metrics(ctx: StockContext) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"₹{ctx.current_price or 'N/A'}")
    col2.metric("52W High", f"₹{ctx.week_52_high  or 'N/A'}")
    col3.metric("52W Low", f"₹{ctx.week_52_low   or 'N/A'}")
    st.success(f"**{ctx.long_name}** | {ctx.sector}")


def _render_messages() -> None:
    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])


def _handle_input(provider: BaseProvider, model: str) -> None:
    user_input = st.chat_input("Ask about financials, valuation, risks, growth...")

    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.spinner(f"{provider.provider_name} / {model}..."):
        try:
            reply = provider.chat(model, st.session_state.messages)
        except Exception as e:
            reply = f"⚠️ {provider.provider_name} error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
