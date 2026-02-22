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
        interval = "d" if timeframe == "1d" else "60"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i={interval}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(payload)))
        bars = []
        for r in rows:
            if not r.get("Close"):
                continue
            ts = r.get("Date", "")
            if timeframe == "1d":
                ts += "T00:00:00Z"
            else:
                ts = r.get("Date") + "T" + r.get("Time", "00:00:00") + "Z"
            bars.append(
                Bar(
                    timestamp=ts,
                    open=float(r["Open"]),
                    high=float(r["High"]),
                    low=float(r["Low"]),
                    close=float(r["Close"]),
                    volume=float(r["Volume"]),
                )
            )
        return bars[-limit:]
