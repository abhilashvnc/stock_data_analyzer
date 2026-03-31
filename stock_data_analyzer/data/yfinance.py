import yfinance as yf
from .base import BaseDataSource, StockContext, FetchResult


class YFinanceSource(BaseDataSource):

    def __init__(self):
        super().__init__("yfinance")

    def fetch(self, ticker: str) -> FetchResult:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or len(info.keys()) <= 1:
                return FetchResult(success=False, error=f"No data found for {ticker}")

            def g(k):
                return info.get(k)

            def safe(fn):
                try:
                    return fn()
                except:
                    return "N/A"

            ctx = StockContext(
                ticker=ticker,
                source=self.source_name,
                long_name=g("longName"),
                sector=g("sector"),
                industry=g("industry"),
                exchange=g("exchange"),
                currency=g("currency"),
                website=g("website"),
                current_price=g("currentPrice"),
                week_52_high=g("fiftyTwoWeekHigh"),
                week_52_low=g("fiftyTwoWeekLow"),
                market_cap=g("marketCap"),
                beta=g("beta"),
                trailing_pe=g("trailingPE"),
                forward_pe=g("forwardPE"),
                peg_ratio=g("pegRatio"),
                price_to_book=g("priceToBook"),
                profit_margin=g("profitMargins"),
                roe=g("returnOnEquity"),
                roa=g("returnOnAssets"),
                ebitda=g("ebitda"),
                free_cashflow=g("freeCashflow"),
                revenue_growth=g("revenueGrowth"),
                earnings_growth=g("earningsGrowth"),
                total_revenue=g("totalRevenue"),
                debt_to_equity=g("debtToEquity"),
                current_ratio=g("currentRatio"),
                total_cash=g("totalCash"),
                total_debt=g("totalDebt"),
                dividend_yield=g("dividendYield"),
                payout_ratio=g("payoutRatio"),
                recommendation=g("recommendationKey"),
                target_mean=g("targetMeanPrice"),
                analyst_count=g("numberOfAnalystOpinions"),
                news=safe(
                    lambda: "\n".join(
                        f"- {n['content']['title']}" for n in (stock.news or [])[:5]
                    )
                ),
                rec_summary=safe(lambda: stock.recommendations.tail(5).to_string()),
                income_stmt=safe(lambda: stock.financials.iloc[:, :2].to_string()),
                cash_flow=safe(lambda: stock.cashflow.iloc[:, :2].to_string()),
                balance_sheet=safe(lambda: stock.balance_sheet.iloc[:, :2].to_string()),
                business_summary=g("longBusinessSummary") or "N/A",
            )
            return FetchResult(success=True, context=ctx)

        except Exception as e:
            return FetchResult(success=False, error=str(e))

    def build_prompt(self, ctx: StockContext) -> str:
        def f(v):
            return str(v) if v is not None else "N/A"

        return f"""
You are a professional stock analyst specializing in Indian equities.
Answer ONLY based on the data provided. If something is missing, say so clearly.

===== COMPANY OVERVIEW =====
Name: {f(ctx.long_name)} | Sector: {f(ctx.sector)} | Industry: {f(ctx.industry)}
Exchange: {f(ctx.exchange)} | Currency: {f(ctx.currency)}

===== PRICE & MARKET =====
Price: {f(ctx.current_price)} | 52W High: {f(ctx.week_52_high)} | 52W Low: {f(ctx.week_52_low)}
Market Cap: {f(ctx.market_cap)} | Beta: {f(ctx.beta)}

===== VALUATION =====
Trailing PE: {f(ctx.trailing_pe)} | Forward PE: {f(ctx.forward_pe)}
PEG: {f(ctx.peg_ratio)} | P/B: {f(ctx.price_to_book)}

===== PROFITABILITY =====
Profit Margin: {f(ctx.profit_margin)} | ROE: {f(ctx.roe)} | ROA: {f(ctx.roa)}
EBITDA: {f(ctx.ebitda)} | FCF: {f(ctx.free_cashflow)}

===== GROWTH =====
Revenue Growth: {f(ctx.revenue_growth)} | Earnings Growth: {f(ctx.earnings_growth)}
Revenue TTM: {f(ctx.total_revenue)}

===== FINANCIAL HEALTH =====
D/E: {f(ctx.debt_to_equity)} | Current Ratio: {f(ctx.current_ratio)}
Cash: {f(ctx.total_cash)} | Debt: {f(ctx.total_debt)}

===== DIVIDENDS =====
Yield: {f(ctx.dividend_yield)} | Payout: {f(ctx.payout_ratio)}

===== ANALYST OPINION =====
Recommendation: {f(ctx.recommendation)} | Target Mean: {f(ctx.target_mean)}
Analysts: {f(ctx.analyst_count)}

Recent Recommendations:
{ctx.rec_summary}

===== RECENT NEWS =====
{ctx.news}

===== INCOME STATEMENT =====
{ctx.income_stmt}

===== CASH FLOW =====
{ctx.cash_flow}

===== BALANCE SHEET =====
{ctx.balance_sheet}

===== BUSINESS SUMMARY =====
{ctx.business_summary}
"""
