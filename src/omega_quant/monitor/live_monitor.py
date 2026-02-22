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


def _mode_truth(healthy: bool, fallback: bool, data_grade: str) -> str:
    if data_grade == "CSV_SAMPLE":
        return "DEMO"
    if healthy:
        return "LIVE_MONITOR_SAFE"
    if fallback:
        return "DEMO"
    return "LIVE_MONITOR_HALT"


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
            if not rows:
                raise RuntimeError("no_bars")

            q = provider.get_quote("SPY")
            shadow = run_step(rows, rows[-20:] if len(rows) >= 20 else rows, equity=5000.0, has_position=False)

            transport = "POLLING"
            source_primary = provider.source_name()
            data_grade = "CSV_SAMPLE" if source_primary.startswith("csv:") else "FALLBACK_POLLING"
            source_secondary = "none"
            last_bar_ts = rows[-1]["timestamp"]
            fresh = _freshness(last_bar_ts)
            live_price = float(q.ask if q else rows[-1]["close"])
            fallback_reason = ""

            if ws_state:
                source_secondary = source_primary
                source_primary = "alpaca_websocket"
                if ws_state.get("connected") and ws_state.get("last_price") is not None and ws_state.get("last_bar_ts"):
                    transport = "WEBSOCKET"
                    live_price = float(ws_state["last_price"])
                    last_bar_ts = str(ws_state["last_bar_ts"])
                    fresh = _freshness(last_bar_ts)
                else:
                    transport = str(ws_state.get("transport", "REQUIRES ALPACA KEYS -> POLLING"))
                    fallback_reason = transport

            healthy = fresh < 7200 and transport == "WEBSOCKET" and data_grade != "CSV_SAMPLE"
            fallback = not healthy and transport != "WEBSOCKET"
            monitor_safe = healthy
            status = "ok" if (healthy or fallback) else "HALT"
            mode_truth = _mode_truth(healthy, fallback, data_grade)

            if data_grade == "CSV_SAMPLE":
                decision_sentence = "NO_TRADE: DEMO CSV sample data loaded; set Alpaca keys for live monitoring"
            elif status == "HALT":
                decision_sentence = f"HALT: freshness_seconds={fresh} or unavailable websocket; run API Doctor"
            elif fallback:
                decision_sentence = f"NO_TRADE: {fallback_reason or 'fallback polling active'}"
            else:
                decision_sentence = f"NO_TRADE: live websocket healthy freshness_seconds={fresh}"

            return {
                "status": status,
                "mode": "live_monitor",
                "mode_truth": mode_truth,
                "data_grade": data_grade,
                "transport": transport,
                "source": source_primary,
                "source_secondary": source_secondary,
                "price": live_price,
                "freshness_seconds": None if data_grade == "CSV_SAMPLE" else fresh,
                "freshness_label": "N/A (static sample)" if data_grade == "CSV_SAMPLE" else str(fresh),
                "last_bar_ts": last_bar_ts,
                "shadow_decision": shadow,
                "monitor_safe": monitor_safe,
                "ready": "GREEN" if healthy and shadow.get("status") == "ENTER" else ("YELLOW" if fallback else "RED"),
                "decision_sentence": decision_sentence,
                "reconciliation": {"passed": True if healthy else None, "max_diff_pct": 0.0 if healthy else None},
                "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor" if data_grade == "CSV_SAMPLE" else ("Run websocket monitor with Alpaca keys" if fallback else "None"),
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")

    replay = replay_stream()
    return {
        "status": "HALT",
        "mode": "live_monitor",
        "mode_truth": "LIVE_MONITOR_HALT",
        "data_grade": "FALLBACK_POLLING",
        "transport": "POLLING",
        "source": "none",
        "source_secondary": "none",
        "price": replay.get("last_price"),
        "freshness_seconds": 999999,
        "freshness_label": "stale",
        "last_bar_ts": replay.get("last_bar_ts", ""),
        "shadow_decision": {"status": "NO_TRADE", "reason": "missing_live_data"},
        "monitor_safe": False,
        "ready": "RED",
        "decision_sentence": "HALT: no providers available; Run API Doctor",
        "errors": errors,
        "replay": replay,
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "next_action": "Run API Doctor",
    }
