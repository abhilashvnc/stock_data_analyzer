from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields


@dataclass
class StockContext:
    ticker: str
    source: str

    long_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    currency: str | None = None
    website: str | None = None

    current_price: float | None = None
    week_52_high: float | None = None
    week_52_low: float | None = None
    market_cap: float | None = None
    beta: float | None = None

    trailing_pe: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None

    profit_margin: float | None = None
    roe: float | None = None
    roa: float | None = None
    ebitda: float | None = None
    free_cashflow: float | None = None

    revenue_growth: float | None = None
    earnings_growth: float | None = None
    total_revenue: float | None = None

    debt_to_equity: float | None = None
    current_ratio: float | None = None
    total_cash: float | None = None
    total_debt: float | None = None

    dividend_yield: float | None = None
    payout_ratio: float | None = None

    recommendation: str | None = None
    target_mean: float | None = None
    analyst_count: int | None = None

    # Text blocks — concatenated across sources
    news: str = "N/A"
    rec_summary: str = "N/A"
    income_stmt: str = "N/A"
    cash_flow: str = "N/A"
    balance_sheet: str = "N/A"
    business_summary: str = "N/A"

    extras: dict = field(default_factory=dict)

    # Text block field names — used by merge
    TEXT_BLOCKS: tuple = field(
        default=(
            "news",
            "rec_summary",
            "income_stmt",
            "cash_flow",
            "balance_sheet",
            "business_summary",
        ),
        init=False,
        repr=False,
        compare=False,
    )

    @classmethod
    def merge(cls, contexts: list["StockContext"]) -> "StockContext":
        """
        Merge multiple StockContext objects into one.
        - Scalar fields: first non-None value wins
        - Text blocks: concatenated with [source] label headers
        - source field: comma-joined list of all sources
        """
        if not contexts:
            raise ValueError("Cannot merge empty list of contexts")

        if len(contexts) == 1:
            return contexts[0]

        base = contexts[0]
        merged_source = ", ".join(c.source for c in contexts)

        # Scalar fields — first non-None wins
        scalar_kwargs: dict = {}
        scalar_fields = [
            f.name
            for f in fields(cls)
            if f.name
            not in (
                "ticker",
                "source",
                "extras",
                "news",
                "rec_summary",
                "income_stmt",
                "cash_flow",
                "balance_sheet",
                "business_summary",
                "TEXT_BLOCKS",
            )
        ]
        for field_name in scalar_fields:
            for ctx in contexts:
                val = getattr(ctx, field_name)
                if val is not None:
                    scalar_kwargs[field_name] = val
                    break
            else:
                scalar_kwargs[field_name] = None

        # Text blocks — concatenate with source label
        text_block_names = [
            "news",
            "rec_summary",
            "income_stmt",
            "cash_flow",
            "balance_sheet",
            "business_summary",
        ]
        text_kwargs: dict = {}
        for block in text_block_names:
            parts = []
            for ctx in contexts:
                val = getattr(ctx, block)
                if val and val != "N/A":
                    parts.append(f"[{ctx.source}]\n{val}")
            text_kwargs[block] = "\n\n".join(parts) if parts else "N/A"

        # Merge extras dicts
        merged_extras: dict = {}
        for ctx in contexts:
            merged_extras.update(ctx.extras)

        return cls(
            ticker=base.ticker,
            source=merged_source,
            extras=merged_extras,
            **scalar_kwargs,
            **text_kwargs,
        )


@dataclass
class FetchResult:
    success: bool
    context: StockContext | None = None
    error: str | None = None


class BaseDataSource(ABC):

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def fetch(self, ticker: str) -> FetchResult: ...

    @abstractmethod
    def build_prompt(self, context: StockContext) -> str: ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
