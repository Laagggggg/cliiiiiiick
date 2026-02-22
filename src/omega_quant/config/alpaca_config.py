from __future__ import annotations

import os
from urllib.parse import urlparse

from omega_quant.ops.env_loader import load_dotenv_if_present


DEFAULT_TRADING_BASE_URL = "https://paper-api.alpaca.markets"
DEFAULT_DATA_BASE_URL = "https://data.alpaca.markets"
DEFAULT_WS_URL = "wss://stream.data.alpaca.markets/v2/iex"


def _valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return bool(p.scheme in {"http", "https", "ws", "wss"} and p.netloc)
    except Exception:  # noqa: BLE001
        return False


def get_alpaca_config() -> dict:
    load_dotenv_if_present()
    key = os.getenv("ALPACA_API_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET", "")
    trading = os.getenv("ALPACA_BASE_URL", DEFAULT_TRADING_BASE_URL)
    data = os.getenv("ALPACA_DATA_BASE_URL", DEFAULT_DATA_BASE_URL)
    ws = os.getenv("ALPACA_WS_URL", DEFAULT_WS_URL)

    warnings: list[str] = []
    if not os.getenv("ALPACA_DATA_BASE_URL"):
        warnings.append("ALPACA_DATA_BASE_URL defaulted")
    if not os.getenv("ALPACA_WS_URL"):
        warnings.append("ALPACA_WS_URL defaulted")

    for name, val in [("ALPACA_BASE_URL", trading), ("ALPACA_DATA_BASE_URL", data), ("ALPACA_WS_URL", ws)]:
        if not _valid_url(val):
            warnings.append(f"invalid_url:{name}")

    return {
        "api_key": key,
        "api_secret": secret,
        "trading_base_url": trading,
        "data_base_url": data,
        "ws_url": ws,
        "keys_present": bool(key and secret),
        "warnings": warnings,
        "missing_vars": [k for k, ok in {"ALPACA_API_KEY": bool(key), "ALPACA_API_SECRET": bool(secret), "ALPACA_BASE_URL": bool(trading), "ALPACA_DATA_BASE_URL": bool(data), "ALPACA_WS_URL": bool(ws)}.items() if not ok],
    }
