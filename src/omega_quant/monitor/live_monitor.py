from __future__ import annotations

from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step


def run_live_monitor() -> dict:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars("SPY", "1h", limit=50)
            rows = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
            shadow = run_step(rows, equity=5000.0)
            readiness = "GREEN" if shadow.get("status") == "TRADE_FILLED" else "YELLOW"
            if shadow.get("status") == "HALT":
                readiness = "RED"
            return {
                "status": "ok",
                "mode": "live_monitor",
                "source": provider.source_name(),
                "latest_bar": rows[-1],
                "shadow_decision": {
                    "status": shadow.get("status"),
                    "reason": shadow.get("reason"),
                    "score": shadow.get("score", 0.0),
                    "threshold": shadow.get("threshold", 0.0),
                    "regime": shadow.get("regime", "UNKNOWN"),
                },
                "readiness": readiness,
                "monitor_safe": True,
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")
    return {"status": "HALT", "mode": "live_monitor", "errors": errors, "readiness": "RED", "monitor_safe": True}
