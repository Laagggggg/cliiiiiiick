from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider
from omega_quant.data.providers.base import Bar, MarketDataProvider, Quote
from omega_quant.data.providers.csv_provider import CsvMarketDataProvider
from omega_quant.data.providers.stooq_provider import StooqDailyProvider


def get_provider_chain() -> list[MarketDataProvider]:
    return [AlpacaMarketDataProvider(), StooqDailyProvider(), CsvMarketDataProvider()]


__all__ = [
    "Bar",
    "Quote",
    "MarketDataProvider",
    "AlpacaMarketDataProvider",
    "CsvMarketDataProvider",
    "StooqDailyProvider",
    "get_provider_chain",
]
