from __future__ import annotations

import hashlib
import time

from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider
from omega_quant.engine import run_step
from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.paper_account.db import (
    append_equity_point,
    close_position,
    get_account_summary,
    get_checkpoint,
    get_open_position,
    open_position,
    set_checkpoint,
)

DB_PATH = "artifacts/paper_account.sqlite"
CP_KEY = "broker_daemon:last_processed_bar_ts:SPY:1h"


def _client_order_id(symbol: str, action: str, ts: str, qty: float) -> str:
    base = f"oq-{symbol}-{action}-{ts}-{qty:.6f}"
    return hashlib.sha1(base.encode()).hexdigest()[:40]


def _broker_qty(positions: list[dict], symbol: str = "SPY") -> float:
    for p in positions:
        if p.get("symbol") == symbol:
            return abs(float(p.get("qty", 0.0)))
    return 0.0


def _step_once(broker: AlpacaPaperBroker, provider: AlpacaMarketDataProvider) -> dict:
    bars_1h = provider.get_bars("SPY", "1h", limit=120)
    rows_1h = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1h]
    bars_1d = provider.get_bars("SPY", "1d", limit=80)
    rows_1d = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1d]

    bar = rows_1h[-1]
    last = get_checkpoint(CP_KEY, DB_PATH)
    if last == bar["timestamp"]:
        return {"status": "SKIP", "reason": "same_bar_checkpoint", "bar_ts": bar["timestamp"]}

    append_equity_point(bar["timestamp"], float(bar["close"]), DB_PATH)

    acct = get_account_summary(DB_PATH)
    pos = get_open_position("SPY", DB_PATH)
    d = run_step(rows_1h, rows_1d, equity=float(acct["equity"]), has_position=bool(pos), entry_price=(pos or {}).get("avg_entry"), hold_bars=0)

    broker_positions = broker.list_positions()
    open_orders = broker.list_orders(status="open", limit=50)

    # reconciliation mismatch guard
    local_qty = float(pos["qty"]) if pos else 0.0
    remote_qty = _broker_qty(broker_positions, "SPY")
    if abs(local_qty - remote_qty) > 1e-6 and not open_orders:
        return {"status": "HALT", "reason": "RECON_MISMATCH", "local_qty": local_qty, "remote_qty": remote_qty, "bar_ts": bar["timestamp"]}

    if d["status"] == "ENTER" and not pos:
        coid = _client_order_id("SPY", "buy", bar["timestamp"], float(d["qty"]))
        existing = broker.get_order_by_client_id(coid)
        detail = existing if existing else broker.place_market_order("SPY", "buy", float(d["qty"]), client_order_id=coid)
        oid = detail.get("id")
        od = broker.get_order(oid) if oid else detail
        q = float(od.get("filled_qty") or d["qty"])
        px = float(od.get("filled_avg_price") or bar["close"])
        open_position(bar["timestamp"], "SPY", q, px, abs(px * q * 0.0005), DB_PATH)
        set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
        return {"status": "ENTER", "order_id": oid, "client_order_id": coid, "qty": q, "price": px, "bar_ts": bar["timestamp"], "reconciliation": {"broker_positions": len(broker_positions), "open_orders": len(open_orders)}}

    if d["status"] == "EXIT" and pos:
        coid = _client_order_id("SPY", "sell", bar["timestamp"], float(pos["qty"]))
        existing = broker.get_order_by_client_id(coid)
        detail = existing if existing else broker.place_market_order("SPY", "sell", float(pos["qty"]), client_order_id=coid)
        oid = detail.get("id")
        od = broker.get_order(oid) if oid else detail
        q = float(od.get("filled_qty") or pos["qty"])
        px = float(od.get("filled_avg_price") or bar["close"])
        close_position(bar["timestamp"], "SPY", px, abs(px * q * 0.0005), {"reason": d["reason"], "mode": "BROKER FILLS"}, DB_PATH)
        set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
        return {"status": "EXIT", "order_id": oid, "client_order_id": coid, "qty": q, "price": px, "bar_ts": bar["timestamp"], "reconciliation": {"broker_positions": len(broker_positions), "open_orders": len(open_orders)}}

    set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
    return {"status": d["status"], "reason": d.get("reason"), "bar_ts": bar["timestamp"], "reconciliation": {"broker_positions": len(broker_positions), "open_orders": len(open_orders)}}


def run_broker_paper_daemon(seconds: int = 30, interval_s: int = 5) -> dict:
    broker = AlpacaPaperBroker()
    if not broker.enabled():
        return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA"}

    provider = AlpacaMarketDataProvider()
    actions: list[dict] = []
    start = time.time()
    while time.time() - start < max(1, seconds):
        try:
            actions.append(_step_once(broker, provider))
        except Exception as exc:  # noqa: BLE001
            actions.append({"status": "HALT", "reason": str(exc)})
        time.sleep(max(1, interval_s))

    return {"status": "ok", "mode_truth": "BROKER FILLS", "actions": actions, "account": get_account_summary(DB_PATH)}
