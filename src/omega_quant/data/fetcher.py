from __future__ import annotations

"""Deprecated: prefer provider-based market data access.

Use `omega_quant.data.providers.get_provider_chain()` and provider.get_bars().
"""

from omega_quant.data.providers import get_provider_chain


def load_market_rows(symbol: str = "SPY", timeframe: str = "1h", limit: int = 300) -> list[dict]:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars(symbol, timeframe, limit=limit)
            return [
                {"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume}
                for b in bars
            ]
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
    raise RuntimeError("unable to fetch rows: " + " | ".join(errors))
