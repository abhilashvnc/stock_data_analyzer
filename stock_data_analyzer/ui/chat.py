import streamlit as st
from providers.base import BaseProvider
from data.base import BaseDataSource, StockContext


def render_chat(provider: BaseProvider, data_sources: list[BaseDataSource]) -> None:
    sess = st.session_state.provider_sessions[st.session_state.active_provider]
    selected_model = sess.get("selected_model")

    ticker_input = st.text_input(
        "Enter Stock Ticker (e.g. RELIANCE, TCS, INFY)",
        key="ticker_input",
    )

    if not ticker_input:
        return

    ticker = _normalise_ticker(ticker_input)

    # Reset only on ticker change — data source changes do NOT reset chat
    if st.session_state.get("fetch_key") != ticker:
        with st.spinner("Fetching stock data..."):
            ctx = _fetch_and_merge(ticker, data_sources)

        if ctx is None:
            return

        st.session_state.fetch_key = ticker
        st.session_state.stock_ctx = ctx
        # System prompt is rebuilt from whichever source is primary (first in list)
        st.session_state.system_prompt = data_sources[0].build_prompt(ctx)
        st.session_state.messages = [
            {"role": "system", "content": st.session_state.system_prompt}
        ]

    else:
        # Ticker unchanged — check if active data sources changed
        # If so, silently update the system prompt without clearing chat history
        ctx = st.session_state.stock_ctx
        if ctx is not None:
            new_prompt = data_sources[0].build_prompt(
                _fetch_and_merge(ticker, data_sources) or ctx
            )
            if new_prompt != st.session_state.system_prompt:
                st.session_state.system_prompt = new_prompt
                # Update system message in history without wiping chat
                if st.session_state.messages:
                    st.session_state.messages[0]["content"] = new_prompt

    ctx = st.session_state.get("stock_ctx")
    if ctx is None:
        return

    _render_metrics(ctx)

    if not selected_model:
        st.warning("⚠️ No model selected. Refresh the model list in the sidebar.")
        return

    _render_messages()
    _handle_input(provider, selected_model)


# ==============================
# HELPERS
# ==============================
def _fetch_and_merge(
    ticker: str,
    data_sources: list[BaseDataSource],
) -> StockContext | None:
    """Fetch from all active sources and merge into one context."""
    contexts = []
    errors = []

    for source in data_sources:
        result = source.fetch(ticker)
        if result.success and result.context:
            contexts.append(result.context)
        else:
            errors.append(f"{source.source_name}: {result.error}")

    if not contexts:
        st.error("❌ All data sources failed:\n" + "\n".join(errors))
        return None

    if errors:
        # Partial failure — warn but continue with what we have
        st.warning("⚠️ Some sources failed:\n" + "\n".join(errors))

    return StockContext.merge(contexts)


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
    st.success(f"**{ctx.long_name}** | {ctx.sector} | *via {ctx.source}*")


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
