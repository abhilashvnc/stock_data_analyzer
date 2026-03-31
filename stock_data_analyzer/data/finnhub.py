import finnhub
from datetime import date, timedelta
from .base import BaseDataSource, StockContext, FetchResult


class FinnhubSource(BaseDataSource):

    def __init__(self, api_key: str):
        super().__init__("finnhub")
        self._client = finnhub.Client(api_key=api_key)

    def fetch(self, ticker: str) -> FetchResult:
        # Finnhub uses symbol without exchange suffix for Indian stocks
        # RELIANCE.NS -> RELIANCE, but NSE-listed stocks need "NSE:RELIANCE"
        symbol = self._to_finnhub_symbol(ticker)

        try:
            profile = self._safe(lambda: self._client.company_profile2(symbol=symbol))
            quote = self._safe(lambda: self._client.quote(symbol))
            financials = self._safe(
                lambda: self._client.company_basic_financials(symbol, "all")
            )
            news = self._safe(
                lambda: self._client.company_news(
                    symbol,
                    _from=(date.today() - timedelta(days=7)).isoformat(),
                    to=date.today().isoformat(),
                )
            )
            rec = self._safe(lambda: self._client.recommendation_trends(symbol))
            peers = self._safe(lambda: self._client.company_peers(symbol))
            earnings = self._safe(
                lambda: self._client.company_earnings(symbol, limit=4)
            )

            if not profile and not quote:
                return FetchResult(
                    success=False, error=f"No Finnhub data found for {symbol}"
                )

            metrics = (financials or {}).get("metric", {})

            # Build news text
            news_text = "N/A"
            if news:
                lines = [
                    f"- {n.get('headline', '')} ({n.get('source', '')})\n"
                    f"  {n.get('summary', '')[:200]}"
                    for n in news[:5]
                ]
                news_text = "\n".join(lines)

            # Build recommendation summary
            rec_text = "N/A"
            if rec:
                latest = rec[:3]
                lines = [
                    f"{r.get('period')}: "
                    f"StrongBuy={r.get('strongBuy')} Buy={r.get('buy')} "
                    f"Hold={r.get('hold')} Sell={r.get('sell')} "
                    f"StrongSell={r.get('strongSell')}"
                    for r in latest
                ]
                rec_text = "\n".join(lines)

            # Build earnings summary
            earnings_text = "N/A"
            if earnings:
                lines = [
                    f"{e.get('period')}: "
                    f"Actual={e.get('actual')} "
                    f"Estimate={e.get('estimate')} "
                    f"Surprise={e.get('surprisePercent', 0):.1f}%"
                    for e in earnings
                ]
                earnings_text = "\n".join(lines)

            # Peers
            peers_text = ", ".join(peers[:6]) if peers else "N/A"

            ctx = StockContext(
                ticker=ticker,
                source=self.source_name,
                long_name=(profile or {}).get("name"),
                sector=(profile or {}).get("finnhubIndustry"),
                industry=(profile or {}).get("finnhubIndustry"),
                exchange=(profile or {}).get("exchange"),
                currency=(profile or {}).get("currency"),
                website=(profile or {}).get("weburl"),
                current_price=(quote or {}).get("c"),  # current price
                week_52_high=metrics.get("52WeekHigh"),
                week_52_low=metrics.get("52WeekLow"),
                market_cap=(profile or {}).get("marketCapitalization"),
                beta=metrics.get("beta"),
                trailing_pe=metrics.get("peBasicExclExtraTTM"),
                forward_pe=metrics.get("peTTM"),
                peg_ratio=metrics.get("pegRatio"),
                price_to_book=metrics.get("pbQuarterly"),
                profit_margin=metrics.get("netProfitMarginTTM"),
                roe=metrics.get("roeTTM"),
                roa=metrics.get("roaTTM"),
                ebitda=metrics.get("ebitdaInterimCagr5Y"),
                free_cashflow=metrics.get("freeCashFlowTTM"),
                revenue_growth=metrics.get("revenueGrowthTTMYoy"),
                earnings_growth=metrics.get("epsGrowthTTMYoy"),
                total_revenue=metrics.get("revenueTTM"),
                debt_to_equity=metrics.get("totalDebt/totalEquityQuarterly"),
                current_ratio=metrics.get("currentRatioQuarterly"),
                total_cash=metrics.get("cashAndEquivalentsQuarterly"),
                total_debt=metrics.get("totalDebtQuarterly"),
                dividend_yield=metrics.get("dividendYieldIndicatedAnnual"),
                payout_ratio=metrics.get("payoutRatioTTM"),
                recommendation=None,  # Finnhub gives counts not a single label
                target_mean=None,  # requires premium on Finnhub
                analyst_count=None,
                news=news_text,
                rec_summary=rec_text,
                income_stmt=earnings_text,  # repurpose for earnings surprises
                cash_flow="N/A",  # not available on free tier
                balance_sheet="N/A",
                business_summary=(profile or {}).get("description", "N/A"),
                extras={
                    "peers": peers_text,
                    "ipo_date": (profile or {}).get("ipo"),
                    "shares_outstanding": (profile or {}).get("shareOutstanding"),
                    "logo": (profile or {}).get("logo"),
                },
            )
            return FetchResult(success=True, context=ctx)

        except Exception as e:
            return FetchResult(success=False, error=str(e))

    def build_prompt(self, ctx: StockContext) -> str:
        def f(v):
            return str(v) if v is not None else "N/A"

        peers = ctx.extras.get("peers", "N/A")
        ipo = ctx.extras.get("ipo_date", "N/A")
        shares = ctx.extras.get("shares_outstanding", "N/A")

        return f"""
You are a professional stock analyst specializing in Indian equities.
Answer ONLY based on the data provided. If something is missing, say so clearly.
Data sourced from Finnhub.

===== COMPANY OVERVIEW =====
Name: {f(ctx.long_name)} | Sector: {f(ctx.sector)}
Exchange: {f(ctx.exchange)} | Currency: {f(ctx.currency)}
IPO Date: {f(ipo)} | Shares Outstanding: {f(shares)}
Website: {f(ctx.website)}

===== PRICE & MARKET =====
Current Price: {f(ctx.current_price)}
52W High: {f(ctx.week_52_high)} | 52W Low: {f(ctx.week_52_low)}
Market Cap (mn): {f(ctx.market_cap)} | Beta: {f(ctx.beta)}

===== VALUATION =====
PE (TTM): {f(ctx.trailing_pe)} | Forward PE: {f(ctx.forward_pe)}
PEG: {f(ctx.peg_ratio)} | P/B: {f(ctx.price_to_book)}

===== PROFITABILITY =====
Net Profit Margin (TTM): {f(ctx.profit_margin)}
ROE (TTM): {f(ctx.roe)} | ROA (TTM): {f(ctx.roa)}
FCF (TTM): {f(ctx.free_cashflow)}

===== GROWTH =====
Revenue Growth (TTM YoY): {f(ctx.revenue_growth)}
EPS Growth (TTM YoY): {f(ctx.earnings_growth)}
Revenue (TTM): {f(ctx.total_revenue)}

===== FINANCIAL HEALTH =====
Debt/Equity: {f(ctx.debt_to_equity)} | Current Ratio: {f(ctx.current_ratio)}
Cash: {f(ctx.total_cash)} | Total Debt: {f(ctx.total_debt)}

===== DIVIDENDS =====
Dividend Yield: {f(ctx.dividend_yield)} | Payout Ratio: {f(ctx.payout_ratio)}

===== ANALYST RECOMMENDATIONS (recent) =====
{ctx.rec_summary}

===== EARNINGS SURPRISES (last 4 quarters) =====
{ctx.income_stmt}

===== RECENT NEWS =====
{ctx.news}

===== PEER COMPANIES =====
{peers}

===== BUSINESS DESCRIPTION =====
{ctx.business_summary}
"""

    # ==============================
    # HELPERS
    # ==============================
    @staticmethod
    def _to_finnhub_symbol(ticker: str) -> str:
        """
        Convert yfinance-style ticker to Finnhub format.
        RELIANCE.NS  -> NSE:RELIANCE
        RELIANCE.BO  -> BSE:RELIANCE
        RELIANCE     -> NSE:RELIANCE  (assume NSE)
        """
        if ticker.endswith(".NS"):
            return "NSE:" + ticker[:-3]
        if ticker.endswith(".BO"):
            return "BSE:" + ticker[:-3]
        return "NSE:" + ticker

    @staticmethod
    def _safe(fn):
        try:
            return fn()
        except Exception:
            return None
