from __future__ import annotations

import csv
from pathlib import Path

from omega_quant.data.providers.base import Bar, MarketDataProvider


class CsvMarketDataProvider(MarketDataProvider):
    def __init__(self, path: str = "data/spy_1h_sample.csv") -> None:
        raw = Path(path)
        if raw.is_absolute():
            self.path = raw
        else:
            repo_root = Path(__file__).resolve().parents[4]
            self.path = repo_root / raw

    def source_name(self) -> str:
        return f"csv:{self.path}"

    def get_bars(self, symbol: str, timeframe: str, limit: int = 300) -> list[Bar]:
        if not self.path.exists():
            raise FileNotFoundError(f"missing market data csv: {self.path}")
        with self.path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        bars = [
            Bar(
                timestamp=r["timestamp"],
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r["volume"]),
            )
            for r in rows
        ]
        return bars[-limit:]
