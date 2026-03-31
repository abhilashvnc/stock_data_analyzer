from .base import BaseDataSource, StockContext, FetchResult
from .yfinance import YFinanceSource

__all__ = [
    "BaseDataSource",
    "StockContext",
    "FetchResult",
    "YFinanceSource",
]

# Registry — plug in new sources here
DATA_SOURCE_REGISTRY: dict[str, BaseDataSource] = {
    "yfinance": YFinanceSource(),
    # "moneycontrol": MoneyControlSource(),   # future
    # "nse":          NSESource(),            # future
}
