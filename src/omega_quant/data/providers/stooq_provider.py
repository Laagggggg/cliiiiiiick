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
            date_str = r.get("Date", "")
            time_str = r.get("Time", "00:00:00")
            # Stooq US data is in US/Eastern; store as explicit offset
            # EST = UTC-5, EDT = UTC-4.  Use -05:00 as conservative default.
            if timeframe == "1d":
                ts = date_str + "T00:00:00-05:00"
            else:
                ts = date_str + "T" + time_str + "-05:00"
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
