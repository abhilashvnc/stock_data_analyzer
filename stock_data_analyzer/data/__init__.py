import os
from .base import BaseDataSource, StockContext, FetchResult
from .yfinance import YFinanceSource
from .finnhub import FinnhubSource

__all__ = [
    "BaseDataSource",
    "StockContext",
    "FetchResult",
    "YFinanceSource",
    "FinnhubSource",
]


def build_registry() -> dict[str, BaseDataSource]:
    registry: dict[str, BaseDataSource] = {
        "yfinance": YFinanceSource(),  # always available
    }

    finnhub_key = os.getenv("FINNHUB_API_KEY", "")
    if finnhub_key:
        registry["finnhub"] = FinnhubSource(api_key=finnhub_key)

    return registry


DATA_SOURCE_REGISTRY: dict[str, BaseDataSource] = build_registry()
