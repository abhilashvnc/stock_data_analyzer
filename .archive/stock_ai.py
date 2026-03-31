import ollama
import yfinance as yf

# Choose stock
stock = yf.Ticker("RELIANCE.NS")

# Get data
info = stock.info

# Prompt for AI
prompt = f"""
You are a professional stock analyst.

Analyze this company:

Name: {info.get('longName')}
Sector: {info.get('sector')}
Market Cap: {info.get('marketCap')}
Revenue Growth: {info.get('revenueGrowth')}

Give:
- Business summary
- Strengths
- Risks
- Long-term investment view
"""

# Send to Ollama
response = ollama.chat(
    model="mistral",
    messages=[{"role": "user", "content": prompt}]
)

print(response['message']['content'])