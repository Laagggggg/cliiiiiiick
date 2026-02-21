from __future__ import annotations

"""Provider-first fetcher facade.

Deprecated old CSV-only loader in favor of provider chain.
"""

from omega_quant.data.providers import get_provider_chain


def load_market_rows(symbol: str = "SPY", timeframe: str = "1h", limit: int = 300) -> list[dict]:
    errs: list[str] = []
    for p in get_provider_chain():
        try:
            bars = p.get_bars(symbol, timeframe, limit=limit)
            return [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
        except Exception as exc:  # noqa: BLE001
            errs.append(f"{p.source_name()}:{exc}")
    raise RuntimeError("unable to fetch rows: " + " | ".join(errs))
