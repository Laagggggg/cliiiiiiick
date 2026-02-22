from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from omega_quant.config.alpaca_config import get_alpaca_config
from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step
from omega_quant.monitor.live_ws import ensure_websocket, get_ws_state, replay_stream

CACHE_DIR = Path("artifacts")


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def compute_freshness(*, data_grade: str, bar_ts: str = "", quote_ts: str = "", trade_ts: str = "", cache_ts: str = "", ws_mode: bool = False) -> dict:
    if data_grade == "CSV_SAMPLE":
        return {"freshness_seconds": None, "freshness_label": "N/A (static sample)", "freshness_basis": "static_sample"}

    now = datetime.now(timezone.utc)
    basis = "bar_ts"
    ts = bar_ts
    if data_grade == "CACHED":
        basis = "cache_ts"
        ts = cache_ts or bar_ts
    elif ws_mode:
        if bar_ts:
            basis, ts = "bar_ts", bar_ts
        elif quote_ts:
            basis, ts = "quote_ts", quote_ts
        elif trade_ts:
            basis, ts = "trade_ts", trade_ts

    dt = _parse_ts(ts)
    if not dt:
        return {"freshness_seconds": 999999, "freshness_label": "STALE", "freshness_basis": basis}
    fresh = int((now - dt).total_seconds())
    label = "OK" if fresh <= 7200 else "STALE"
    return {"freshness_seconds": fresh, "freshness_label": label, "freshness_basis": basis}


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


def _provider_label(source_name: str) -> str:
    if source_name.startswith("csv:"):
        return "CSV_SAMPLE"
    if source_name.startswith("cache:"):
        return "CACHE_SPY_1H"
    if source_name == "alpaca":
        return "ALPACA_BARS"
    return source_name.upper()


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

            bars_loaded = len(rows)
            q = provider.get_quote("SPY")
            shadow = run_step(rows, rows[-20:] if len(rows) >= 20 else rows, equity=5000.0, has_position=False)
            source_primary = _provider_label(provider.source_name())
            data_grade = "CSV_SAMPLE" if source_primary == "CSV_SAMPLE" else "FALLBACK_POLLING"
            source_secondary = "none"
            transport = "POLLING"
            last_bar_ts = rows[-1]["timestamp"]
            live_price = float(q.ask if q else rows[-1]["close"])
            quote_ts = ""
            trade_ts = ""

            if ws_state:
                source_secondary = source_primary
                source_primary = "ALPACA_WEBSOCKET"
                if ws_state.get("connected") and ws_state.get("last_price") is not None:
                    transport = "WEBSOCKET"
                    live_price = float(ws_state["last_price"])
                    quote_ts = str(ws_state.get("last_quote_ts", ""))
                    trade_ts = str(ws_state.get("last_trade_ts", ""))
                    if ws_state.get("last_bar_ts"):
                        last_bar_ts = str(ws_state.get("last_bar_ts"))
                else:
                    transport = str(ws_state.get("transport", "REQUIRES ALPACA KEYS -> POLLING"))

            if data_grade == "CSV_SAMPLE":
                transport = "POLLING"
            fresh = compute_freshness(data_grade=data_grade, bar_ts=last_bar_ts, quote_ts=quote_ts, trade_ts=trade_ts, ws_mode=(transport == "WEBSOCKET"))
            healthy = (fresh["freshness_seconds"] is not None and fresh["freshness_seconds"] <= 7200 and data_grade != "CSV_SAMPLE" and (transport == "WEBSOCKET" or transport == "POLLING"))
            mode_truth = "DEMO" if data_grade == "CSV_SAMPLE" else ("LIVE_MONITOR_SAFE" if healthy else "LIVE_MONITOR_HALT")
            status = "ok" if (healthy or data_grade == "CSV_SAMPLE") else "HALT"
            if data_grade == "CSV_SAMPLE":
                sentence = "NO_TRADE: demo CSV sample active. Next: set Alpaca keys and run API Doctor."
            elif status == "HALT":
                sentence = f"HALT: {fresh['freshness_label']} using {fresh['freshness_basis']}. Next: run API Doctor and monitor."
            else:
                sentence = f"NO_TRADE: live feed healthy ({fresh['freshness_basis']}={fresh['freshness_seconds']}s). Next: keep monitor running."

            cfg = get_alpaca_config()
            alpaca_ok = source_primary in {"ALPACA_BARS", "ALPACA_WEBSOCKET"}
            return {
                "status": status,
                "mode": "live_monitor",
                "mode_truth": mode_truth,
                "data_grade": data_grade,
                "transport": transport,
                "source": source_primary,
                "source_secondary": source_secondary,
                "price": live_price,
                "freshness_seconds": fresh["freshness_seconds"],
                "freshness_label": fresh["freshness_label"],
                "freshness_basis": fresh["freshness_basis"],
                "last_bar_ts": last_bar_ts,
                "shadow_decision": shadow,
                "monitor_safe": healthy,
                "decision_sentence": sentence,
                "reconciliation": {"passed": True if healthy else None, "max_diff_pct": 0.0 if healthy else None},
                "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor" if data_grade == "CSV_SAMPLE" else ("Run websocket monitor and keep data fresh" if not healthy else "None"),
                "keys_present": cfg.get("keys_present", False),
                "ws_health": "connected" if (ws_state and ws_state.get("connected")) else "disconnected",
                "alpaca_call_succeeded": alpaca_ok,
                "bars_loaded": bars_loaded,
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")

    cache = _read_cache("SPY", "1h")
    if cache and cache.get("rows"):
        rows = cache["rows"]
        last_bar_ts = rows[-1]["timestamp"]
        fresh = compute_freshness(data_grade="CACHED", cache_ts=last_bar_ts)
        return {
            "status": "HALT",
            "mode": "live_monitor",
            "mode_truth": "SAFE_DEGRADED",
            "data_grade": "CACHED",
            "transport": "POLLING",
            "source": "CACHE_SPY_1H",
            "source_secondary": "none",
            "price": float(rows[-1]["close"]),
            "freshness_seconds": fresh["freshness_seconds"],
            "freshness_label": fresh["freshness_label"],
            "freshness_basis": fresh["freshness_basis"],
            "last_bar_ts": last_bar_ts,
            "shadow_decision": {"status": "NO_TRADE", "reason": "cached_data_only"},
            "monitor_safe": False,
            "decision_sentence": "HALT: provider outage, cached bars only. Next: restore providers and rerun API Doctor.",
            "errors": errors,
            "reconciliation": {"passed": None, "max_diff_pct": None},
            "next_action": "Restore providers/websocket and rerun API Doctor",
            "keys_present": get_alpaca_config().get("keys_present", False),
            "ws_health": "disconnected",
            "alpaca_call_succeeded": False,
            "bars_loaded": len(rows),
        }

    replay = replay_stream()
    fresh = compute_freshness(data_grade="FALLBACK_POLLING", bar_ts=replay.get("last_bar_ts", ""))
    return {
        "status": "HALT",
        "mode": "live_monitor",
        "mode_truth": "LIVE_MONITOR_HALT",
        "data_grade": "FALLBACK_POLLING",
        "transport": "POLLING",
        "source": "none",
        "source_secondary": "none",
        "price": replay.get("last_price"),
        "freshness_seconds": fresh["freshness_seconds"],
        "freshness_label": fresh["freshness_label"],
        "freshness_basis": fresh["freshness_basis"],
        "last_bar_ts": replay.get("last_bar_ts", ""),
        "shadow_decision": {"status": "NO_TRADE", "reason": "missing_live_data"},
        "monitor_safe": False,
        "decision_sentence": "HALT: no providers available. Next: run API Doctor.",
        "errors": errors,
        "replay": replay,
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "next_action": "Run API Doctor",
        "keys_present": get_alpaca_config().get("keys_present", False),
        "ws_health": "disconnected",
        "alpaca_call_succeeded": False,
        "bars_loaded": 0,
    }
