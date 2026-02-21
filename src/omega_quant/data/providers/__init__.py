from omega_quant.data.providers.base import Bar, MarketDataProvider
from omega_quant.data.providers.csv_provider import CsvMarketDataProvider
from omega_quant.data.providers.stooq_provider import StooqDailyProvider


def get_provider_chain() -> list[MarketDataProvider]:
    return [StooqDailyProvider(), CsvMarketDataProvider()]


__all__ = [
    "Bar",
    "MarketDataProvider",
    "CsvMarketDataProvider",
    "StooqDailyProvider",
    "get_provider_chain",
]
