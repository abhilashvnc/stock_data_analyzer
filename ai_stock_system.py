import yfinance as yf
import pandas as pd
import ollama
import streamlit as st

# ==============================
# FUNCTION 1: GET STOCK DATA
# ==============================
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info


# ==============================
# FUNCTION 2: PRINT DATA
# ==============================
def show_stock_details(info):
    # info = get_stock_data(ticker)

    print("\n📊", info.get("symbol"))
    print("Name:", info.get("longName"))
    print("PE:", info.get("trailingPE"))
    print("ROE:", info.get("returnOnEquity"))
    print("Growth:", info.get("revenueGrowth"))


# ==============================
# FUNCTION 3: AI ANALYSIS
# ==============================
def analyze_with_ai(info):

    prompt = f"""
    Analyze this company:

    Name: {info.get('longName')}
    PE: {info.get('trailingPE')}
    ROE: {info.get('returnOnEquity')}
    Growth: {info.get('revenueGrowth')}
    PriceToBook: {info.get('priceToBook')}
    Eps: {info.get('trailingEps')}
    CurrentPrice: {info.get('currentPrice')}
    trailingPegRatio: {info.get('trailingPegRatio')}
    
    
    

    Give investment insights.
    """

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    print("\n🤖 AI Analysis:\n")
    print(response['message']['content'])
    
    
def chat_with_ai():
    st.title("📈 AI Stock Analyst")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input
    while True:
        user_input = st.chat_input("Ask about stocks...")       

        if user_input:
            
            if user_input.lower() == "exit":
                break
            
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)

            response = ollama.chat(
                model="mistral",
                messages=st.session_state.messages
            )

            ai_reply = response["message"]["content"]

            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.chat_message("assistant").write(ai_reply)


# ==============================
# MAIN CONTROL
# ==============================

def main():
    ticker = input("Enter stock ticker (eg: TCS.NS): ")
    if not ticker:
        raise("Error: Ticker undefined")
    ticker = ticker.upper()
    ticker = ticker + ".NS" if not ticker.endswith(".NS") else ticker

    info = get_stock_data(ticker)
    print("Abhilash", info)
    if not info.get("trailingPegRatio", None) and len(info.keys()) <=1:
        raise("No info Found of ticker")

    show_stock_details(info)
    analyze_with_ai(info)
    
    
# if __name__ == '__main__':
#     while True:
#         main()

chat_with_ai()