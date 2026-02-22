from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Quote:
    timestamp: str
    bid: float
    ask: float


class MarketDataProvider:
    def get_bars(self, symbol: str, timeframe: str, limit: int = 300) -> list[Bar]:
        raise NotImplementedError

    def get_latest_bar(self, symbol: str, timeframe: str) -> Bar:
        bars = self.get_bars(symbol=symbol, timeframe=timeframe, limit=1)
        return bars[-1]

    def get_quote(self, symbol: str) -> Quote | None:
        return None

    def source_name(self) -> str:
        raise NotImplementedError
