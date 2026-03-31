import streamlit as st
from providers.base import BaseProvider
from data.base import BaseDataSource


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

    with st.spinner("Fetching stock data..."):
        fetch_result = data_source.fetch(ticker)

    if not fetch_result.success or fetch_result.context is None:
        st.error(f"❌ {fetch_result.error}")
        return

    ctx = fetch_result.context
    _render_metrics(ctx)

    if not selected_model:
        st.warning("⚠️ No model selected. Refresh the model list in the sidebar.")
        return

    # Build system prompt from data source
    system_prompt = data_source.build_prompt(ctx)

    # Reset chat if ticker, provider, or model changed
    chat_key = f"{ticker}__{st.session_state.active_provider}__{selected_model}"
    if st.session_state.chat_key != chat_key:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.chat_key = chat_key

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


def _render_metrics(ctx) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"₹{ctx.current_price  or 'N/A'}")
    col2.metric("52W High", f"₹{ctx.week_52_high   or 'N/A'}")
    col3.metric("52W Low", f"₹{ctx.week_52_low    or 'N/A'}")
    st.success(f"**{ctx.long_name}** | {ctx.sector}")


def _render_messages() -> None:
    for msg in st.session_state.messages[1:]:  # skip system prompt
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
