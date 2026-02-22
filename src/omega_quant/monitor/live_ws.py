from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omega_quant.config.alpaca_config import get_alpaca_config


ARTIFACTS = Path("artifacts")
STREAM_JOURNAL = ARTIFACTS / "live_stream.jsonl"


@dataclass
class WSState:
    connected: bool = False
    reconnecting: bool = False
    failed: bool = False
    transport: str = "POLLING"
    error: str = ""
    last_price: float | None = None
    last_quote_ts: str = ""
    last_trade_ts: str = ""
    last_bar_ts: str = ""
    updated_at: float = 0.0


_STATE = WSState()
_THREAD: threading.Thread | None = None
_LOCK = threading.Lock()


def _journal_row(row: dict[str, Any]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with STREAM_JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def _set_status(**kwargs: Any) -> None:
    with _LOCK:
        for key, value in kwargs.items():
            setattr(_STATE, key, value)


def _normalize_event(msg: dict[str, Any]) -> dict[str, Any] | None:
    tpe = str(msg.get("T", "")).lower()
    recv_ts = time.time()

    # Alpaca Market Data v2 event types: q=quote, t=trade, b=bar
    # Ref: https://docs.alpaca.markets/docs/streaming-market-data
    if tpe == "q":
        bid = msg.get("bp")
        ask = msg.get("ap")
        if bid is None and ask is None:
            return None
        return {
            "schema": "alpaca.marketdata.v2",
            "kind": "quote",
            "event_ts": str(msg.get("t", "")),
            "symbol": str(msg.get("S", "SPY")),
            "bid": float(bid) if bid is not None else None,
            "ask": float(ask) if ask is not None else None,
            "price": float(ask if ask is not None else bid),
            "recv_ts": recv_ts,
            "raw": msg,
        }

    if tpe == "t":
        price = msg.get("p")
        size = msg.get("s")
        if price is None:
            return None
        return {
            "schema": "alpaca.marketdata.v2",
            "kind": "trade",
            "event_ts": str(msg.get("t", "")),
            "symbol": str(msg.get("S", "SPY")),
            "price": float(price),
            "size": float(size) if size is not None else None,
            "recv_ts": recv_ts,
            "raw": msg,
        }

    if tpe == "b":
        if any(msg.get(k) is None for k in ["o", "h", "l", "c", "v"]):
            return None
        return {
            "schema": "alpaca.marketdata.v2",
            "kind": "bar",
            "event_ts": str(msg.get("t", "")),
            "symbol": str(msg.get("S", "SPY")),
            "open": float(msg["o"]),
            "high": float(msg["h"]),
            "low": float(msg["l"]),
            "close": float(msg["c"]),
            "volume": float(msg["v"]),
            "price": float(msg["c"]),
            "recv_ts": recv_ts,
            "raw": msg,
        }

    return None


def _apply_normalized(event: dict[str, Any]) -> None:
    kind = event["kind"]
    price = event.get("price")
    event_ts = str(event.get("event_ts", ""))
    with _LOCK:
        _STATE.updated_at = time.time()
        if price is not None:
            _STATE.last_price = float(price)
        if kind == "quote":
            _STATE.last_quote_ts = event_ts
        elif kind == "trade":
            _STATE.last_trade_ts = event_ts
        elif kind == "bar":
            _STATE.last_bar_ts = event_ts


def _ingest_raw(msg: dict[str, Any]) -> None:
    event = _normalize_event(msg)
    if not event:
        return
    _apply_normalized(event)
    _journal_row(event)


async def _run_ws(symbol: str, max_messages: int | None = None) -> None:
    import websockets  # type: ignore

    cfg = get_alpaca_config()
    key = cfg["api_key"]
    secret = cfg["api_secret"]
    endpoint = cfg["ws_url"]

    if not key or not secret:
        reason = "REQUIRES ALPACA KEYS -> POLLING"
        _set_status(connected=False, failed=True, transport=reason, error=reason)
        _journal_row({"schema": "alpaca.marketdata.v2", "kind": "status", "event_ts": "", "state": "keys_missing", "transport": reason, "recv_ts": time.time()})
        return

    backoff_s = 1
    seen = 0
    while True:
        try:
            _set_status(reconnecting=True, transport="WEBSOCKET", error="")
            # websockets keepalive guidance: ping_interval + ping_timeout to detect dead peers.
            # Ref: https://websockets.readthedocs.io/en/stable/topics/keepalive.html
            async with websockets.connect(endpoint, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                await ws.send(json.dumps({"action": "subscribe", "quotes": [symbol], "trades": [symbol], "bars": [symbol]}))
                _set_status(connected=True, reconnecting=False, failed=False, error="", transport="WEBSOCKET")
                _journal_row({"schema": "alpaca.marketdata.v2", "kind": "status", "event_ts": "", "state": "connected", "transport": "WEBSOCKET", "recv_ts": time.time()})
                backoff_s = 1

                async for raw in ws:
                    try:
                        payload = json.loads(raw)
                    except Exception:
                        continue
                    items = payload if isinstance(payload, list) else [payload]
                    for msg in items:
                        if isinstance(msg, dict):
                            _ingest_raw(msg)
                            seen += 1
                            if max_messages is not None and seen >= max_messages:
                                return

        except Exception as exc:  # noqa: BLE001
            reason = f"WEBSOCKET FAILED -> POLLING ({exc})"
            _set_status(connected=False, reconnecting=True, failed=True, transport=reason, error=str(exc))
            _journal_row({"schema": "alpaca.marketdata.v2", "kind": "status", "event_ts": "", "state": "disconnected", "transport": reason, "recv_ts": time.time()})
            await asyncio.sleep(min(30, backoff_s))
            backoff_s = min(30, backoff_s * 2)


def _thread_main(symbol: str) -> None:
    try:
        asyncio.run(_run_ws(symbol))
    except Exception as exc:  # noqa: BLE001
        _set_status(connected=False, failed=True, transport="WEBSOCKET FAILED -> POLLING", error=str(exc))


def ensure_websocket(symbol: str = "SPY") -> dict[str, Any]:
    global _THREAD
    cfg = get_alpaca_config()
    key = cfg["api_key"]
    secret = cfg["api_secret"]
    if not key or not secret:
        reason = "REQUIRES ALPACA KEYS -> POLLING"
        _set_status(connected=False, reconnecting=False, failed=True, transport=reason, error=reason)
        return {"ok": False, "transport": reason, "state": get_ws_state()}
    if _THREAD is None or not _THREAD.is_alive():
        _THREAD = threading.Thread(target=_thread_main, args=(symbol,), daemon=True)
        _THREAD.start()
    st = get_ws_state()
    return {"ok": st["connected"], "transport": st["transport"], "state": st}


def replay_stream(path: str = str(STREAM_JOURNAL)) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {
            "status": "WARN",
            "reason": "stream_journal_missing",
            "next_action": "Run websocket monitor",
            "events": 0,
            "last_price": None,
            "last_bar_ts": "",
        }

    rebuilt = {
        "last_price": None,
        "last_quote_ts": "",
        "last_trade_ts": "",
        "last_bar_ts": "",
        "events": 0,
    }

    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rebuilt["events"] += 1
        kind = row.get("kind")
        if kind in {"quote", "trade", "bar"} and row.get("price") is not None:
            rebuilt["last_price"] = float(row["price"])
        if kind == "quote":
            rebuilt["last_quote_ts"] = str(row.get("event_ts", ""))
        elif kind == "trade":
            rebuilt["last_trade_ts"] = str(row.get("event_ts", ""))
        elif kind == "bar":
            rebuilt["last_bar_ts"] = str(row.get("event_ts", ""))

    if rebuilt["events"] == 0:
        return {
            "status": "WARN",
            "reason": "empty_stream_journal",
            "next_action": "Run websocket monitor",
            **rebuilt,
        }

    return {"status": "ok", "transport": "REPLAY", **rebuilt}


def get_ws_state() -> dict[str, Any]:
    with _LOCK:
        return {
            "connected": _STATE.connected,
            "reconnecting": _STATE.reconnecting,
            "failed": _STATE.failed,
            "transport": _STATE.transport,
            "error": _STATE.error,
            "last_price": _STATE.last_price,
            "last_quote_ts": _STATE.last_quote_ts,
            "last_trade_ts": _STATE.last_trade_ts,
            "last_bar_ts": _STATE.last_bar_ts,
            "updated_at": _STATE.updated_at,
        }
