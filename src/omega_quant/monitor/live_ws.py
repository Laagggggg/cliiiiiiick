from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from dataclasses import dataclass


@dataclass
class WSState:
    connected: bool = False
    reconnecting: bool = False
    failed: bool = False
    transport: str = "POLLING"
    error: str = ""
    last_price: float | None = None
    last_ts: str = ""
    updated_at: float = 0.0


_STATE = WSState()
_THREAD: threading.Thread | None = None
_LOCK = threading.Lock()


def _apply_quote(msg: dict) -> None:
    # Alpaca quotes: {"T":"q","bp":...,"ap":...,"t":"..."}
    bid = msg.get("bp")
    ask = msg.get("ap")
    ts = msg.get("t", "")
    if bid is None and ask is None:
        return
    price = float(ask if ask is not None else bid)
    with _LOCK:
        _STATE.last_price = price
        _STATE.last_ts = ts
        _STATE.updated_at = time.time()


def _set_status(**kwargs) -> None:
    with _LOCK:
        for k, v in kwargs.items():
            setattr(_STATE, k, v)


async def _run_ws(symbol: str) -> None:
    import websockets  # type: ignore

    key = os.getenv("ALPACA_API_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET", "")
    endpoint = os.getenv("ALPACA_WS_URL", "wss://stream.data.alpaca.markets/v2/iex")
    if not key or not secret:
        _set_status(connected=False, failed=True, transport="WEBSOCKET FAILED -> POLLING", error="missing_alpaca_keys")
        return

    backoff = 1
    while True:
        try:
            _set_status(reconnecting=True, transport="WEBSOCKET")
            async with websockets.connect(endpoint, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                await ws.send(json.dumps({"action": "subscribe", "quotes": [symbol]}))
                _set_status(connected=True, reconnecting=False, failed=False, error="", transport="WEBSOCKET")
                backoff = 1
                async for raw in ws:
                    try:
                        payload = json.loads(raw)
                    except Exception:
                        continue
                    items = payload if isinstance(payload, list) else [payload]
                    for msg in items:
                        if msg.get("T") == "q":
                            _apply_quote(msg)
        except Exception as exc:  # noqa: BLE001
            _set_status(connected=False, reconnecting=True, failed=True, transport="WEBSOCKET FAILED -> POLLING", error=str(exc))
            await asyncio.sleep(min(30, backoff))
            backoff = min(30, backoff * 2)


def _thread_main(symbol: str) -> None:
    try:
        asyncio.run(_run_ws(symbol))
    except Exception as exc:  # noqa: BLE001
        _set_status(connected=False, failed=True, transport="WEBSOCKET FAILED -> POLLING", error=str(exc))


def ensure_websocket(symbol: str = "SPY") -> dict:
    global _THREAD
    if _THREAD is None or not _THREAD.is_alive():
        _THREAD = threading.Thread(target=_thread_main, args=(symbol,), daemon=True)
        _THREAD.start()
    with _LOCK:
        return {
            "ok": _STATE.connected,
            "transport": _STATE.transport,
            "state": {
                "connected": _STATE.connected,
                "reconnecting": _STATE.reconnecting,
                "failed": _STATE.failed,
                "error": _STATE.error,
                "last_price": _STATE.last_price,
                "last_ts": _STATE.last_ts,
                "updated_at": _STATE.updated_at,
            },
        }


def get_ws_state() -> dict:
    with _LOCK:
        return {
            "connected": _STATE.connected,
            "reconnecting": _STATE.reconnecting,
            "failed": _STATE.failed,
            "transport": _STATE.transport,
            "error": _STATE.error,
            "last_price": _STATE.last_price,
            "last_ts": _STATE.last_ts,
            "updated_at": _STATE.updated_at,
        }
