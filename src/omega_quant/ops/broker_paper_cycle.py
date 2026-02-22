from __future__ import annotations

from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider
from omega_quant.engine import run_step
from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.paper_account.db import close_position, get_account_summary, get_open_position, open_position

DB_PATH = "artifacts/paper_account.sqlite"


def run_broker_paper_cycle(steps: int = 1) -> dict:
    broker = AlpacaPaperBroker()
    if not broker.enabled():
        return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA"}

    provider = AlpacaMarketDataProvider()
    bars_1h = provider.get_bars("SPY", "1h", limit=100)
    rows_1h = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1h]
    bars_1d = provider.get_bars("SPY", "1d", limit=60)
    rows_1d = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars_1d]

    actions = []
    for _ in range(max(1, steps)):
        acct = get_account_summary(DB_PATH)
        pos = get_open_position("SPY", DB_PATH)
        d = run_step(rows_1h, rows_1d, equity=float(acct["equity"]), has_position=bool(pos), entry_price=(pos or {}).get("avg_entry"), hold_bars=0)
        if d["status"] == "ENTER":
            order = broker.place_market_order("SPY", "buy", d["qty"])
            oid = order.get("id")
            detail = broker.get_order(oid) if oid else order
            px = float(detail.get("filled_avg_price") or rows_1h[-1]["close"])
            q = float(detail.get("filled_qty") or d["qty"])
            open_position(rows_1h[-1]["timestamp"], "SPY", q, px, abs(px * q * 0.0005), DB_PATH)
            actions.append({"status": "ENTER", "order_id": oid, "qty": q, "price": px})
        elif d["status"] == "EXIT" and pos:
            order = broker.place_market_order("SPY", "sell", pos["qty"])
            oid = order.get("id")
            detail = broker.get_order(oid) if oid else order
            px = float(detail.get("filled_avg_price") or rows_1h[-1]["close"])
            close_position(rows_1h[-1]["timestamp"], "SPY", px, abs(px * pos["qty"] * 0.0005), {"reason": d["reason"], "mode": "BROKER FILLS"}, DB_PATH)
            actions.append({"status": "EXIT", "order_id": oid, "qty": pos["qty"], "price": px})
        else:
            actions.append({"status": d["status"], "reason": d.get("reason")})

    return {"status": "ok", "mode_truth": "BROKER FILLS", "actions": actions, "account": get_account_summary(DB_PATH)}
