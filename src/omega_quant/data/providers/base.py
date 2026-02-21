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


class MarketDataProvider:
    def get_bars(self, symbol: str, timeframe: str, limit: int = 300) -> list[Bar]:
        raise NotImplementedError

    def source_name(self) -> str:
        raise NotImplementedError
