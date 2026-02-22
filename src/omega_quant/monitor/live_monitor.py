from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step
from omega_quant.monitor.live_ws import ensure_websocket, get_ws_state, replay_stream


CACHE_DIR = Path("artifacts")


def _freshness(ts: str) -> int:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:  # noqa: BLE001
        return 999999


def _cache_path(symbol: str, timeframe: str) -> Path:
    return CACHE_DIR / f"cache_{symbol}_{timeframe}.json"


def _write_cache(symbol: str, timeframe: str, rows: list[dict], source: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(symbol, timeframe).write_text(json.dumps({"symbol": symbol, "timeframe": timeframe, "source": source, "rows": rows}, indent=2), encoding="utf-8")


def _read_cache(symbol: str, timeframe: str) -> dict | None:
    p = _cache_path(symbol, timeframe)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _mode_truth(healthy: bool, fallback: bool, data_grade: str) -> str:
    if data_grade == "CSV_SAMPLE":
        return "DEMO"
    if data_grade == "CACHED":
        return "SAFE_DEGRADED"
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
            _write_cache("SPY", "1h", rows, provider.source_name())

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
            status = "ok" if (healthy or fallback) else "HALT"
            if data_grade == "CSV_SAMPLE":
                sentence = "NO_TRADE: NOT LIVE DATA (CSV sample); set Alpaca keys"
            elif status == "HALT":
                sentence = f"HALT: freshness_seconds={fresh} or unavailable websocket"
            elif fallback:
                sentence = f"NO_TRADE: {fallback_reason or 'fallback polling active'}"
            else:
                sentence = f"NO_TRADE: live websocket healthy freshness_seconds={fresh}"

            return {
                "status": status,
                "mode": "live_monitor",
                "mode_truth": _mode_truth(healthy, fallback, data_grade),
                "data_grade": data_grade,
                "transport": transport,
                "source": source_primary,
                "source_secondary": source_secondary,
                "price": live_price,
                "freshness_seconds": None if data_grade == "CSV_SAMPLE" else fresh,
                "freshness_label": "N/A (static sample)" if data_grade == "CSV_SAMPLE" else str(fresh),
                "last_bar_ts": last_bar_ts,
                "shadow_decision": shadow,
                "monitor_safe": healthy,
                "ready": "GREEN" if healthy and shadow.get("status") == "ENTER" else ("YELLOW" if fallback else "RED"),
                "decision_sentence": sentence,
                "reconciliation": {"passed": True if healthy else None, "max_diff_pct": 0.0 if healthy else None},
                "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor" if data_grade == "CSV_SAMPLE" else ("Run websocket monitor with Alpaca keys" if fallback else "None"),
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")

    cache = _read_cache("SPY", "1h")
    if cache and cache.get("rows"):
        rows = cache["rows"]
        last_bar_ts = rows[-1]["timestamp"]
        fresh = _freshness(last_bar_ts)
        return {
            "status": "HALT",
            "mode": "live_monitor",
            "mode_truth": "SAFE_DEGRADED",
            "data_grade": "CACHED",
            "transport": "POLLING",
            "source": f"cache:{_cache_path('SPY', '1h')}",
            "source_secondary": "none",
            "price": float(rows[-1]["close"]),
            "freshness_seconds": fresh,
            "freshness_label": str(fresh),
            "last_bar_ts": last_bar_ts,
            "shadow_decision": {"status": "NO_TRADE", "reason": "cached_data_only"},
            "monitor_safe": False,
            "ready": "RED",
            "decision_sentence": "HALT: providers failed; using cached bars only",
            "errors": errors,
            "reconciliation": {"passed": None, "max_diff_pct": None},
            "next_action": "Restore providers/websocket and rerun API Doctor",
        }

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
        "decision_sentence": "HALT: no providers available",
        "errors": errors,
        "replay": replay,
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "next_action": "Run API Doctor",
    }
