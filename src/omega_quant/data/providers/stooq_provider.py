from __future__ import annotations

import csv
import io
import urllib.request

from omega_quant.data.providers.base import Bar, MarketDataProvider


class StooqDailyProvider(MarketDataProvider):
    def source_name(self) -> str:
        return "stooq_daily"

    def get_bars(self, symbol: str, timeframe: str, limit: int = 300) -> list[Bar]:
        stooq_symbol = symbol.lower() + ".us"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(payload)))
        bars = [
            Bar(
                timestamp=r["Date"] + "T00:00:00Z",
                open=float(r["Open"]),
                high=float(r["High"]),
                low=float(r["Low"]),
                close=float(r["Close"]),
                volume=float(r["Volume"]),
            )
            for r in rows
            if r.get("Close")
        ]
        return bars[-limit:]
