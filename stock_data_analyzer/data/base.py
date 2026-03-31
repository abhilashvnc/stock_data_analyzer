from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StockContext:
    """
    Normalised container that every data source must fill.
    The AI prompt is built from this — not from raw source data.
    This decouples the prompt from any specific data provider.
    """
    ticker:         str
    source:         str                     # e.g. "yfinance", "moneycontrol"

    # Core fields — all optional since not every source has everything
    long_name:      str | None = None
    sector:         str | None = None
    industry:       str | None = None
    exchange:       str | None = None
    currency:       str | None = None
    website:        str | None = None

    current_price:  float | None = None
    week_52_high:   float | None = None
    week_52_low:    float | None = None
    market_cap:     float | None = None
    beta:           float | None = None

    trailing_pe:    float | None = None
    forward_pe:     float | None = None
    peg_ratio:      float | None = None
    price_to_book:  float | None = None

    profit_margin:  float | None = None
    roe:            float | None = None
    roa:            float | None = None
    ebitda:         float | None = None
    free_cashflow:  float | None = None

    revenue_growth: float | None = None
    earnings_growth:float | None = None
    total_revenue:  float | None = None

    debt_to_equity: float | None = None
    current_ratio:  float | None = None
    total_cash:     float | None = None
    total_debt:     float | None = None

    dividend_yield: float | None = None
    payout_ratio:   float | None = None

    recommendation: str | None = None
    target_mean:    float | None = None
    analyst_count:  int | None = None

    # Free-text blocks
    news:           str = "N/A"
    rec_summary:    str = "N/A"
    income_stmt:    str = "N/A"
    cash_flow:      str = "N/A"
    balance_sheet:  str = "N/A"
    business_summary: str = "N/A"

    # Catch-all for source-specific extras
    extras:         dict = field(default_factory=dict)


@dataclass
class FetchResult:
    success: bool
    context: StockContext | None = None
    error:   str | None = None


class BaseDataSource(ABC):

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def fetch(self, ticker: str) -> FetchResult:
        """
        Fetch all available data for ticker.
        Returns a FetchResult wrapping a normalised StockContext.
        """
        ...

    @abstractmethod
    def build_prompt(self, context: StockContext) -> str:
        """
        Convert a StockContext into the system prompt string for the AI.
        Each source can format this differently if needed.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"