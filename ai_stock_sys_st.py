import yfinance as yf
import ollama
import streamlit as st

# ==============================
# GET STOCK DATA
# ==============================
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info


# ==============================
# FORMAT CONTEXT FOR AI
# ==============================
def build_context(info):
    return f"""
    You are a professional stock analyst.

    Current stock data:
    Name: {info.get('longName')}
    Sector: {info.get('sector')}
    PE: {info.get('trailingPE')}
    ROE: {info.get('returnOnEquity')}
    Revenue Growth: {info.get('revenueGrowth')}
    Profit Margin: {info.get('profitMargins')}
    Debt/Equity: {info.get('debtToEquity')}
    Price: {info.get('currentPrice')}

    raw data (): {info}

    Answer all questions ONLY based on this company.
    """


# ==============================
# STREAMLIT UI
# ==============================
st.title("📈 AI Stock Chat (Ollama)")

# ---- Ticker Input ----
ticker = st.text_input("Enter Stock Ticker (e.g. RELIANCE.NS)")

if ticker:
    ticker = ticker.upper()
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    info = get_stock_data(ticker)

    if not info or len(info.keys()) <= 1:
        st.error("❌ Invalid ticker or no data found")
        st.stop()

    st.success(f"Loaded data for {info.get('longName')}")

    # Build AI context once
    context = build_context(info)

    # Store chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": context}
        ]

    # Show previous chat
    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask anything about this stock...")

    if user_input:
        # Save user message
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        st.chat_message("user").write(user_input)

        # AI response
        response = ollama.chat(
            model="mistral",
            messages=st.session_state.messages
        )

        ai_reply = response["message"]["content"]

        st.session_state.messages.append(
            {"role": "assistant", "content": ai_reply}
        )

        st.chat_message("assistant").write(ai_reply)