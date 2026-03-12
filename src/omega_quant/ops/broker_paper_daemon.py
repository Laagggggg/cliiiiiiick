from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider
from omega_quant.engine import run_step
from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.time.market_hours import market_timezone_status, should_block_new_orders
from omega_quant.paper_account.db import (
    append_equity_point,
    append_order_event,
    append_recon_snapshot,
    close_position,
    export_recon_jsonl,
    get_account_summary,
    get_checkpoint,
    get_latest_order_event_by_client_id,
    get_open_position,
    open_position,
    register_paper_day,
    set_checkpoint,
)

DB_PATH = "artifacts/paper_account.sqlite"
CP_KEY = "broker_daemon:last_processed_bar_ts:SPY:1h"
RECON_JOURNAL = Path("artifacts/recon_snapshots.jsonl")
DAEMON_TICK_JOURNAL = Path("artifacts/daemon_tick_summary.jsonl")
ORDER_STATES = {"new": "NEW", "partially_filled": "PARTIAL", "filled": "FILLED", "canceled": "CANCELED", "rejected": "REJECTED"}


def _client_order_id(symbol: str, action: str, ts: str, qty: float) -> str:
    return hashlib.sha1(f"oq-{symbol}-{action}-{ts}-{qty:.6f}".encode()).hexdigest()[:40]


def _broker_qty(positions: list[dict], symbol: str = "SPY") -> float:
    for p in positions:
        if p.get("symbol") == symbol:
            return abs(float(p.get("qty", 0.0)))
    return 0.0


def _order_state(order: dict) -> str:
    return ORDER_STATES.get(str(order.get("status", "")).lower(), "NEW")


def _append_tick_summary(row: dict) -> None:
    DAEMON_TICK_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with DAEMON_TICK_JOURNAL.open("a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(row, sort_keys=True) + "\n")


def _retry_call(fn, *args, **kwargs):
    delay = 1
    for i in range(4):
        try:
            return fn(*args, **kwargs)
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(delay)
            delay = min(8, delay * 2)




def _parse_order_age_seconds(order: dict) -> int | None:
    ts = order.get("submitted_at") or order.get("created_at")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()))
    except Exception:  # noqa: BLE001
        return None


def _maybe_cancel_stale_orders(broker: AlpacaPaperBroker, open_orders: list[dict]) -> list[dict]:
    max_age = int(os.getenv("MAX_ORDER_AGE_SECONDS", "180"))
    canceled: list[dict] = []
    for o in open_orders:
        age = _parse_order_age_seconds(o)
        if age is None or age <= max_age:
            continue
        oid = str(o.get("id") or "")
        if not oid:
            continue
        broker.cancel_order(oid)
        canceled.append({"order_id": oid, "age_seconds": age, "client_order_id": o.get("client_order_id", "")})
    return canceled


def _safe_get_order_by_client_id(broker: AlpacaPaperBroker, coid: str) -> tuple[dict | None, bool]:
    try:
        return broker.get_order_by_client_id(coid), False
    except Exception:  # noqa: BLE001
        return None, True


def _write_recon_snapshot(ts: str, local_qty: float, remote_qty: float, open_orders: list[dict], account: dict, broker_positions: list[dict]) -> dict:
    mismatch = abs(local_qty - remote_qty) > 1e-6
    has_open_orders = bool(open_orders)
    status = "WARN" if mismatch and has_open_orders else ("FAIL" if mismatch else "PASS")
    snapshot = {
        "local_qty": local_qty,
        "remote_qty": remote_qty,
        "open_orders": len(open_orders),
        "local_equity": float(account.get("equity", 0.0)),
        "local_cash": float(account.get("cash", 0.0)),
        "broker_positions": len(broker_positions),
        "max_diff_pct": abs(local_qty - remote_qty) / max(1.0, abs(local_qty)) * 100.0,
        "passed": not mismatch,
        "status": status,
    }
    append_recon_snapshot(ts, snapshot, DB_PATH)
    export_recon_jsonl(str(RECON_JOURNAL), DB_PATH)
    return snapshot


def _hydrate_startup_state(broker: AlpacaPaperBroker) -> dict:
    try:
        broker_positions = _retry_call(broker.list_positions)
        open_orders = _retry_call(broker.list_orders, status="open", limit=50)
    except Exception as exc:  # noqa: BLE001
        return {"status": "HALT", "reason": "BROKER_BOOTSTRAP_FAILED", "decision_sentence": f"HALT: startup broker sync failed ({exc}). Next: rerun doctor.", "next_action": "Run API Doctor and retry daemon"}
    local = get_open_position("SPY", DB_PATH)
    local_qty = float(local["qty"]) if local else 0.0
    remote_qty = _broker_qty(broker_positions, "SPY")
    mismatch = abs(local_qty - remote_qty) > 1e-6
    if mismatch and not open_orders:
        return {"status": "HALT", "reason": "BOOT_RECON_MISMATCH", "decision_sentence": "HALT: startup reconciliation mismatch with no open orders. Next: flatten/resync.", "next_action": "Flatten positions and rerun daemon"}
    if mismatch and open_orders:
        return {"status": "WARN", "reason": "BOOT_RECON_WARN", "decision_sentence": "WARN: startup mismatch with open orders. Next: allow fills to settle.", "next_action": "Monitor open orders"}
    return {"status": "ok", "reason": "BOOT_SYNC_OK", "decision_sentence": "OK: startup broker/local state aligned. Next: daemon loop running.", "next_action": "None"}


def _step_once(broker: AlpacaPaperBroker, provider: AlpacaMarketDataProvider) -> dict:
    bars_1h = provider.get_bars("SPY", "1h", limit=120)
    rows_1h = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1h]
    bars_1d = provider.get_bars("SPY", "1d", limit=80)
    rows_1d = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1d]

    bar = rows_1h[-1]
    last = get_checkpoint(CP_KEY, DB_PATH)
    if last == bar["timestamp"]:
        return {"status": "SKIP", "reason": "same_bar_checkpoint", "decision_sentence": "SKIP: already processed this bar. Next: wait for a new bar.", "next_action": "Wait for next bar", "bar_ts": bar["timestamp"]}

    append_equity_point(bar["timestamp"], float(bar["close"]), DB_PATH)
    acct = get_account_summary(DB_PATH)
    pos = get_open_position("SPY", DB_PATH)
    decision = run_step(rows_1h, rows_1d, equity=float(acct["equity"]), has_position=bool(pos), entry_price=(pos or {}).get("avg_entry"), hold_bars=0)

    broker_positions = _retry_call(broker.list_positions)
    open_orders = _retry_call(broker.list_orders, status="open", limit=50)
    canceled_stale_orders = _maybe_cancel_stale_orders(broker, open_orders)
    if canceled_stale_orders:
        open_orders = _retry_call(broker.list_orders, status="open", limit=50)
    local_qty = float(pos["qty"]) if pos else 0.0
    remote_qty = _broker_qty(broker_positions, "SPY")
    recon = _write_recon_snapshot(bar["timestamp"], local_qty, remote_qty, open_orders, acct, broker_positions)
    order_ages = [x for x in (_parse_order_age_seconds(o) for o in open_orders) if x is not None]
    max_order_age_seconds = max(order_ages) if order_ages else 0

    if recon["status"] == "FAIL":
        return {"status": "HALT", "reason": "RECON_MISMATCH", "decision_sentence": "HALT: reconciliation mismatch with no open orders. Next: flatten, resync, and rerun doctor.", "next_action": "Check positions, flatten if needed, rerun API Doctor", "bar_ts": bar["timestamp"], "reconciliation": recon}

    warn_msg = None
    if recon["status"] == "WARN":
        warn_msg = "WARN: reconciliation mismatch with open orders; continuing until fills settle. Next: monitor order states."

    if decision["status"] == "ENTER" and not pos:
        tz_status = market_timezone_status()
        if not tz_status.get("ok"):
            set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
            return {"status": "HALT", "reason": tz_status.get("reason", "timezone_missing"), "bar_ts": bar["timestamp"], "reconciliation": recon, "canceled_stale_orders": canceled_stale_orders, "max_order_age_seconds": max_order_age_seconds, "decision_sentence": tz_status.get("decision_sentence", "HALT: market timezone unavailable. Next: install tzdata"), "next_action": tz_status.get("next_action", "Install tzdata (python -m pip install tzdata) and rerun")}
        if should_block_new_orders(bar["timestamp"]):
            set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
            return {"status": "HALT", "reason": "OUTSIDE_RTH", "bar_ts": bar["timestamp"], "reconciliation": recon, "canceled_stale_orders": canceled_stale_orders, "max_order_age_seconds": max_order_age_seconds, "decision_sentence": "HALT: outside RTH. Next: wait for market open or enable EXT_HOURS=true", "next_action": "Wait for 9:30-16:00 ET or set EXT_HOURS=true"}
        coid = _client_order_id("SPY", "buy", bar["timestamp"], float(decision["qty"]))
        remote_existing, lookup_failed = _safe_get_order_by_client_id(broker, coid)
        local_existing = (get_latest_order_event_by_client_id(coid, DB_PATH) or {}).get("payload")
        existing = remote_existing or local_existing
        if lookup_failed and not local_existing:
            return {"status": "HALT", "reason": "BROKER_LOOKUP_UNCERTAIN", "decision_sentence": "HALT: broker lookup failed and no local order record. Next: retry after broker recovery.", "next_action": "Run API Doctor and wait for broker recovery", "bar_ts": bar["timestamp"], "reconciliation": recon}
        detail = existing if existing else _retry_call(broker.place_market_order, "SPY", "buy", float(decision["qty"]), client_order_id=coid)
        oid = str(detail.get("id") or coid)
        od = _retry_call(broker.get_order, oid) if detail.get("id") else detail
        q = float(od.get("filled_qty") or decision["qty"])
        px = float(od.get("filled_avg_price") or bar["close"])
        open_position(bar["timestamp"], "SPY", q, px, abs(px * q * 0.0005), DB_PATH)
        append_order_event(bar["timestamp"], oid, coid, _order_state(od), od, DB_PATH)
        set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
        return {"status": "ENTER", "warning": warn_msg, "order_id": oid, "client_order_id": coid, "qty": q, "price": px, "bar_ts": bar["timestamp"], "reconciliation": recon, "canceled_stale_orders": canceled_stale_orders, "max_order_age_seconds": max_order_age_seconds, "decision_sentence": f"TRADE: entered SPY qty={q:.4f} at {px:.2f}. Next: monitor reconciliation and exits.", "next_action": "Keep daemon running"}

    if decision["status"] == "EXIT" and pos:
        coid = _client_order_id("SPY", "sell", bar["timestamp"], float(pos["qty"]))
        remote_existing, lookup_failed = _safe_get_order_by_client_id(broker, coid)
        local_existing = (get_latest_order_event_by_client_id(coid, DB_PATH) or {}).get("payload")
        existing = remote_existing or local_existing
        if lookup_failed and not local_existing:
            return {"status": "HALT", "reason": "BROKER_LOOKUP_UNCERTAIN", "decision_sentence": "HALT: broker lookup failed and no local order record. Next: retry after broker recovery.", "next_action": "Run API Doctor and wait for broker recovery", "bar_ts": bar["timestamp"], "reconciliation": recon}
        detail = existing if existing else _retry_call(broker.place_market_order, "SPY", "sell", float(pos["qty"]), client_order_id=coid)
        oid = str(detail.get("id") or coid)
        od = _retry_call(broker.get_order, oid) if detail.get("id") else detail
        q = float(od.get("filled_qty") or pos["qty"])
        px = float(od.get("filled_avg_price") or bar["close"])
        close_position(bar["timestamp"], "SPY", px, abs(px * q * 0.0005), {"reason": decision["reason"], "mode": "BROKER FILLS"}, DB_PATH)
        append_order_event(bar["timestamp"], oid, coid, _order_state(od), od, DB_PATH)
        set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
        return {"status": "EXIT", "warning": warn_msg, "order_id": oid, "client_order_id": coid, "qty": q, "price": px, "bar_ts": bar["timestamp"], "reconciliation": recon, "canceled_stale_orders": canceled_stale_orders, "max_order_age_seconds": max_order_age_seconds, "decision_sentence": f"TRADE: exited SPY qty={q:.4f} at {px:.2f}. Next: monitor next signal.", "next_action": "Keep daemon running"}

    set_checkpoint(CP_KEY, bar["timestamp"], DB_PATH)
    reason = decision.get("reason", "no entry condition")
    sentence = f"NO_TRADE: {reason}. Next: keep daemon running for next bar."
    if warn_msg:
        sentence = f"WARN: {warn_msg}"
    return {"status": decision["status"], "warning": warn_msg, "reason": reason, "bar_ts": bar["timestamp"], "reconciliation": recon, "canceled_stale_orders": canceled_stale_orders, "max_order_age_seconds": max_order_age_seconds, "decision_sentence": sentence, "next_action": "Keep daemon running"}


def run_broker_paper_daemon(seconds: int = 30, interval_s: int = 5) -> dict:
    broker = AlpacaPaperBroker()
    if not broker.enabled():
        return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "decision_sentence": "HALT: missing Alpaca keys. Next: set .env keys and run API Doctor.", "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET and rerun API Doctor"}

    provider = AlpacaMarketDataProvider()
    actions: list[dict] = []
    boot = _hydrate_startup_state(broker)
    actions.append(boot)
    _append_tick_summary(boot)
    if boot.get("status") == "HALT":
        return {"status": "HALT", "mode_truth": "BROKER FILLS", "actions": actions, "account": get_account_summary(DB_PATH), "recon_journal": str(RECON_JOURNAL), "tick_journal": str(DAEMON_TICK_JOURNAL), "decision_sentence": boot.get("decision_sentence"), "next_action": boot.get("next_action")}
    start = time.time()
    while time.time() - start < max(1, seconds):
        day = datetime.now(timezone.utc).date().isoformat()
        register_paper_day(day, DB_PATH)
        try:
            tick = _step_once(broker, provider)
            actions.append(tick)
            _append_tick_summary(tick)
        except Exception as exc:  # noqa: BLE001
            tick = {"status": "HALT", "reason": str(exc), "decision_sentence": f"HALT: daemon error {exc}. Next: run API Doctor.", "next_action": "Run API Doctor and inspect broker connectivity"}
            actions.append(tick)
            _append_tick_summary(tick)
        time.sleep(max(1, interval_s))

    return {"status": "ok", "mode_truth": "BROKER FILLS", "actions": actions, "account": get_account_summary(DB_PATH), "recon_journal": str(RECON_JOURNAL), "tick_journal": str(DAEMON_TICK_JOURNAL), "decision_sentence": "ok: broker daemon cycle complete. Next: review actions and reconciliation.", "next_action": "Continue daemon or inspect recon journal"}
