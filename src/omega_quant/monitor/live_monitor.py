from __future__ import annotations

from datetime import datetime, timezone

from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step
from omega_quant.monitor.live_ws import ensure_websocket, get_ws_state, replay_stream


def _freshness(ts: str) -> int:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:  # noqa: BLE001
        return 999999


def _truth_sentence(transport: str, fresh: int, last_bar_ts: str) -> str:
    if fresh >= 7200:
        return f"HALT: freshness_seconds={fresh} exceeds 7200 at {last_bar_ts or 'unknown_ts'}"
    if "FAILED" in transport:
        return f"NO_TRADE: transport={transport} using polling fallback"
    return f"NO_TRADE: monitor healthy freshness_seconds={fresh} last_bar_ts={last_bar_ts}"


def run_live_monitor(mode: str = "polling") -> dict:
    ws_state = None
    if mode == "websocket":
        ensure_websocket("SPY")
        ws_state = get_ws_state()

    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars("SPY", "1h", limit=80)
            rows = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
            q = provider.get_quote("SPY")
            shadow = run_step(rows, rows[-20:] if len(rows) >= 20 else rows, equity=5000.0, has_position=False)
            fresh = _freshness(rows[-1]["timestamp"])
            live_price = q.ask if q else rows[-1]["close"]
            transport = "POLLING"
            last_bar_ts = rows[-1]["timestamp"]

            if ws_state:
                if ws_state.get("connected") and ws_state.get("last_price") is not None:
                    transport = "WEBSOCKET"
                    live_price = ws_state["last_price"]
                    if ws_state.get("last_ts"):
                        fresh = _freshness(ws_state["last_ts"])
                        last_bar_ts = ws_state.get("last_bar_ts") or ws_state["last_ts"]
                else:
                    transport = ws_state.get("transport", "WEBSOCKET FAILED -> POLLING")

            monitor_safe = fresh < 7200 or provider.source_name() != "alpaca"
            ready = "GREEN" if shadow.get("status") == "ENTER" and monitor_safe else ("YELLOW" if monitor_safe else "RED")

            return {
                "status": "ok" if monitor_safe else "HALT",
                "mode": "live_monitor",
                "transport": transport,
                "source": provider.source_name(),
                "price": float(live_price),
                "freshness_seconds": fresh,
                "last_bar_ts": last_bar_ts,
                "shadow_decision": shadow,
                "monitor_safe": monitor_safe,
                "ready": ready,
                "decision_sentence": _truth_sentence(transport, fresh, last_bar_ts),
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")

    replay = replay_stream()
    return {
        "status": "HALT",
        "mode": "live_monitor",
        "transport": "POLLING",
        "source": "none",
        "price": None,
        "freshness_seconds": 999999,
        "last_bar_ts": replay.get("last_bar_ts", ""),
        "shadow_decision": {"status": "NO_TRADE", "reason": "missing_live_data"},
        "monitor_safe": False,
        "ready": "RED",
        "decision_sentence": "HALT: no providers available; run doctor and monitor",
        "errors": errors,
        "replay": replay,
    }
