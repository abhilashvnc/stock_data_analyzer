import pandas as pd
import yfinance as yf
import ollama
from concurrent.futures import ThreadPoolExecutor

# ==============================
# LOAD ALL STOCKS
# ==============================

df_symbols = pd.read_csv("symbols.csv")
tickers = [s + ".NS" for s in df_symbols["SYMBOL"]]

print(f"Total Stocks Loaded: {len(tickers)}")

# ==============================
# FAST FILTER FUNCTION
# ==============================

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        growth = info.get("revenueGrowth")
        debt = info.get("debtToEquity")

        if (
            pe and pe < 50 and
            roe and roe > 0.12 and
            growth and growth > 0.08 and
            debt and debt < 120
        ):
            return {
                "ticker": ticker,
                "name": info.get("longName"),
                "pe": pe,
                "roe": roe,
                "growth": growth,
                "debt": debt
            }

    except:
        return None

# ==============================
# PARALLEL SCANNING (FAST)
# ==============================

results = []

with ThreadPoolExecutor(max_workers=10) as executor:
    data = list(executor.map(analyze_stock, tickers))

results = [r for r in data if r]

print(f"\nFiltered Stocks: {len(results)}")

# ==============================
# TOP 10 SELECTION
# ==============================

df = pd.DataFrame(results)

if df.empty:
    print("No stocks found")
    exit()

df = df.sort_values(by="growth", ascending=False).head(10)

print("\nTop Candidates:\n")
print(df[["ticker","growth","roe"]])

# ==============================
# AI ANALYSIS (ONLY TOP 10)
# ==============================

for _, row in df.iterrows():

    print("\n========================")
    print("AI Analyzing:", row["ticker"])

    prompt = f"""
    Analyze this company:

    Name: {row['name']}
    PE: {row['pe']}
    ROE: {row['roe']}
    Growth: {row['growth']}
    Debt: {row['debt']}

    Give:
    - Strengths
    - Risks
    - Multibagger potential
    """

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    print(response['message']['content'])