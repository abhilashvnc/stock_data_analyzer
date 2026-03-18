import yfinance as yf
import pandas as pd
import ollama

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
    Analyze this stock like a professional investor:

    Name: {info.get('longName')}
    Sector: {info.get('sector')}

    --- Growth ---
    Revenue Growth: {info.get('revenueGrowth')}
    Earnings Growth: {info.get('earningsGrowth')}

    --- Profitability ---
    ROE: {info.get('returnOnEquity')}
    ROA: {info.get('returnOnAssets')}
    Profit Margin: {info.get('profitMargins')}

    --- Valuation ---
    PE: {info.get('trailingPE')}
    Forward PE: {info.get('forwardPE')}
    PEG: {info.get('trailingPegRatio')}
    Price to Book: {info.get('priceToBook')}

    --- Financial Health ---
    Debt to Equity: {info.get('debtToEquity')}
    Current Ratio: {info.get('currentRatio')}
    Free Cash Flow: {info.get('freeCashflow')}

    --- Market ---
    Current Price: {info.get('currentPrice')}
    52 Week High: {info.get('fiftyTwoWeekHigh')}
    52 Week Low: {info.get('fiftyTwoWeekLow')}

    Give:
    1. Strengths
    2. Weaknesses
    3. Valuation opinion
    4. Long-term investment view
    """

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    print("\n🤖 AI Analysis:\n")
    print(response['message']['content'])


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
    
    
while True:
    main()
