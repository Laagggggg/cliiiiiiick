from __future__ import annotations

from datetime import datetime, timezone

from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step


def _freshness(ts: str) -> int:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:  # noqa: BLE001
        return 999999


def run_live_monitor(mode: str = "polling") -> dict:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars("SPY", "1h", limit=80)
            rows = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
            q = provider.get_quote("SPY")
            shadow = run_step(rows, rows[-20:] if len(rows) >= 20 else rows, equity=5000.0, has_position=False)
            fresh = _freshness(rows[-1]["timestamp"])
            ready = "GREEN" if shadow.get("status") == "ENTER" and fresh < 1800 else ("YELLOW" if fresh < 7200 else "RED")
            return {
                "status": "ok",
                "mode": "live_monitor",
                "transport": "POLLING MODE" if mode != "websocket" else "WEBSOCKET REQUESTED (fallback polling)",
                "source": provider.source_name(),
                "latest_bar": rows[-1],
                "live_price": q.ask if q else rows[-1]["close"],
                "spread": (q.ask - q.bid) if q else None,
                "freshness_seconds": fresh,
                "delayed_label": "REALTIME" if provider.source_name() == "alpaca" else "DELAYED/POLL",
                "shadow_decision": {
                    "status": shadow.get("status"),
                    "reason": shadow.get("reason"),
                    "score": shadow.get("score", 0.0),
                    "threshold": shadow.get("threshold", 0.0),
                    "regime": shadow.get("regime", "UNKNOWN"),
                },
                "readiness": ready,
                "monitor_safe": True,
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")
    return {"status": "HALT", "mode": "live_monitor", "transport": "POLLING MODE", "errors": errors, "readiness": "RED", "monitor_safe": True}
