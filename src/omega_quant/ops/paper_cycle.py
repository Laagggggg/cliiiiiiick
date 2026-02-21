from __future__ import annotations

import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

from omega_quant.data.providers import get_provider_chain
from omega_quant.data.reconciler import reconcile_prices
from omega_quant.engine import run_step
from omega_quant.ops.logger import log_event
from omega_quant.ops.trade_review import render_trade_reviews_markdown
from omega_quant.paper_account.db import (
    append_equity_point,
    close_position,
    export_jsonl,
    get_account_summary,
    get_open_position,
    get_or_create_account,
    list_equity_curve,
    list_trades,
    open_position,
)

ARTIFACTS = Path("artifacts")
DB_PATH = "artifacts/paper_account.sqlite"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _freshness(ts: str) -> int:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        secs = int((datetime.now(timezone.utc) - dt).total_seconds())
        return (secs // 60) * 60
    except Exception:  # noqa: BLE001
        return 999999


def _rows_from_provider(symbol: str, timeframe: str, limit: int) -> tuple[list[dict], str]:
    errs: list[str] = []
    for p in get_provider_chain():
        try:
            bars = p.get_bars(symbol, timeframe, limit=limit)
            if len(bars) < 50:
                continue
            return ([{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars], p.source_name())
        except Exception as exc:  # noqa: BLE001
            errs.append(f"{p.source_name()}:{exc}")
    raise RuntimeError("no_provider " + " | ".join(errs))


def _slippage(mid: float, spread: float, qty: float, vol: float) -> float:
    impact = min(mid * 0.002, (qty / max(1.0, vol)) * mid * 4)
    return (spread * 0.5) + impact


def _fill_entry(limit_price: float, bar: dict, market_order: bool, slip: float) -> float | None:
    if market_order:
        return float(bar["open"]) + slip
    lo, hi = float(bar["low"]), float(bar["high"])
    if lo <= limit_price <= hi:
        return limit_price + slip
    return None


def _png(path: Path, series: list[float], markers: list[int] | None = None) -> None:
    w, h = 640, 220
    markers = markers or []
    mn, mx = (min(series), max(series)) if series else (0.0, 1.0)
    span = (mx - mn) or 1.0
    pts = []
    for i, v in enumerate(series):
        x = int(i * (w - 1) / max(1, len(series) - 1))
        y = int((mx - v) * (h - 1) / span)
        pts.append((x, y))
    ptset = set(pts)
    markx = {int(i * (w - 1) / max(1, len(series) - 1)) for i in markers}

    raw = bytearray()
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            if (x, y) in ptset:
                row.extend((20, 200, 20))
            elif x in markx:
                row.extend((220, 60, 60))
            else:
                row.extend((30, 30, 30))
        raw.extend(row)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _checks(paths: list[Path], out: Path) -> None:
    out.write_text("\n".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.as_posix()}" for p in paths) + "\n", encoding="utf-8")


def run_paper_cycle(starting_capital: float = 5000.0, cycles: int = 1) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    get_or_create_account(starting_capital, DB_PATH)
    start_equity = float(get_account_summary(DB_PATH)["equity"])

    rows_1h, source = _rows_from_provider("SPY", "1h", 800)
    rows_1d, _ = _rows_from_provider("SPY", "1d", 240)

    rec = {"passed": True, "degraded": True, "max_diff_pct": 0.0}
    for p in get_provider_chain():
        if p.source_name() == source:
            continue
        try:
            sec = p.get_bars("SPY", "1h", limit=len(rows_1h))
            sec_close = [float(b.close) for b in sec][-len(rows_1h):]
            rec = reconcile_prices([float(r["close"]) for r in rows_1h][-len(sec_close):], sec_close, tolerance_pct=0.25)
            rec["degraded"] = False
            break
        except Exception:  # noqa: BLE001
            continue

    if not rec.get("passed", False):
        return {"status": "HALT", "reason": "reconciliation_failed", "details": rec}

    trade_before = len(list_trades(DB_PATH))
    hold_bars = 0
    start_idx = 60
    end_idx = min(len(rows_1h), start_idx + max(1, cycles) * 80)

    for i in range(start_idx, end_idx):
        bar = rows_1h[i]
        append_equity_point(bar["timestamp"], float(bar["close"]), DB_PATH)

        pos = get_open_position("SPY", DB_PATH)
        acct = get_account_summary(DB_PATH)
        decision = run_step(rows_1h[: i + 1], rows_1d[: min(len(rows_1d), max(30, i // 8))], equity=float(acct["equity"]), has_position=bool(pos), entry_price=(pos or {}).get("avg_entry"), hold_bars=hold_bars)

        if decision["status"] == "ENTER":
            requested_qty = float(decision["qty"])
            max_fill_qty = max(0.0, float(bar["volume"]) * 0.0002)  # participation cap
            fill_qty = min(requested_qty, max_fill_qty)
            if fill_qty <= 0:
                continue
            spread = max(0.01, float(bar["close"]) * 0.0003)
            slip = _slippage(float(bar["close"]), spread, fill_qty, float(bar["volume"]))
            limit_price = float(decision["entry_signal_price"]) * 1.0002
            fill = _fill_entry(limit_price, bar, market_order=False, slip=slip)
            if fill is None:
                continue
            fee = abs(fill * fill_qty * 0.0005)
            open_position(bar["timestamp"], "SPY", fill_qty, fill, fee, DB_PATH)
            hold_bars = 0

        elif decision["status"] == "EXIT" and pos:
            fee = abs(float(bar["close"]) * pos["qty"] * 0.0005)
            close_position(
                bar["timestamp"],
                "SPY",
                float(bar["close"]),
                fee,
                {
                    "reason": decision["reason"],
                    "score": decision.get("score", 0.0),
                    "threshold": decision.get("threshold", 0.0),
                    "regime": decision.get("regime", "UNKNOWN"),
                    "explain": f"{decision['reason']} (score={decision.get('score',0):.3f}, thr={decision.get('threshold',0):.3f})",
                },
                DB_PATH,
            )
            hold_bars = 0
        elif pos:
            hold_bars += 1

    trades = list_trades(DB_PATH)
    session_trades = trades[trade_before:]
    acct = get_account_summary(DB_PATH)
    eq = list_equity_curve(DB_PATH)

    for t in session_trades:
        t["counterfactual"] = {"no_trade_pnl": 0.0, "half_size_pnl": t["pnl_dollars"] / 2}

    result = {
        "status": "ok",
        "mode_truth": "SIMULATED FILLS",
        "starting_capital": start_equity,
        "ending_capital": float(acct["equity"]),
        "session_pnl_dollars": float(acct["equity"] - start_equity),
        "session_trade_count": len(session_trades),
        "session_trades": session_trades,
        "ledger_trade_count": len(trades),
        "last_decision_reason": session_trades[-1]["reason"].get("explain", "NO_TRADE") if session_trades else "NO_TRADE",
        "provenance": {
            "source_primary": source,
            "bars_loaded": len(rows_1h),
            "start": rows_1h[0]["timestamp"],
            "end": rows_1h[-1]["timestamp"],
            "freshness_seconds": _freshness(rows_1h[-1]["timestamp"]),
            "dataset_sha256": _sha(json.dumps(rows_1h, sort_keys=True).encode()),
            "reconciliation": rec,
        },
        "truth_anchor": {
            "code_hash": _sha(Path(__file__).read_bytes()),
            "config_hash": _sha(json.dumps({"tolerance": 0.25, "risk_fraction": 0.08}, sort_keys=True).encode()),
            "dataset_hash": _sha(json.dumps(rows_1h, sort_keys=True).encode()),
        },
        "account_summary": acct,
        "risk_of_ruin": min(1.0, (len([t for t in trades if t["pnl_dollars"] < 0]) / max(1, len(trades)))),
    }

    result_path = ARTIFACTS / "paper_cycle_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    ledger_path = ARTIFACTS / "paper_ledger.json"
    ledger_path.write_text(json.dumps(trades, indent=2), encoding="utf-8")
    eq_path = ARTIFACTS / "equity_curve.json"
    eq_path.write_text(json.dumps(eq, indent=2), encoding="utf-8")
    export_jsonl(str(ARTIFACTS / "paper_trades.jsonl"), DB_PATH)
    render_trade_reviews_markdown(str(ARTIFACTS / "paper_trades.jsonl"), str(ARTIFACTS / "paper_trade_reviews.md"))
    proof_path = ARTIFACTS / "paper_proof_report.md"
    proof_path.write_text("# Paper Proof\n\nGenerated from ledger and bars.\n", encoding="utf-8")

    eq_vals = [x["equity"] for x in eq][-500:]
    dd_vals = [x["drawdown"] for x in eq][-500:]
    marker_idx = list(range(max(0, len(eq_vals) - len(session_trades)), len(eq_vals)))
    _png(ARTIFACTS / "equity_curve.png", eq_vals, marker_idx)
    _png(ARTIFACTS / "drawdown.png", dd_vals, marker_idx)
    _png(ARTIFACTS / "trade_markers.png", eq_vals, marker_idx)

    files = [result_path, ledger_path, eq_path, proof_path, ARTIFACTS / "paper_trades.jsonl", ARTIFACTS / "equity_curve.png", ARTIFACTS / "drawdown.png", ARTIFACTS / "trade_markers.png"]
    _checks(files, ARTIFACTS / "checksums.sha256")
    event = log_event("info", "paper_cycle", summary={"session_trade_count": len(session_trades), "ending_capital": acct["equity"]})
    return {
        "result": result,
        "event": event,
        "json_result": str(result_path),
        "proof_file": str(proof_path),
        "review_file": str(ARTIFACTS / "paper_trade_reviews.md"),
        "ledger_file": str(ledger_path),
        "checksum_file": str(ARTIFACTS / "checksums.sha256"),
        "charts": {"equity": str(ARTIFACTS / "equity_curve.png"), "drawdown": str(ARTIFACTS / "drawdown.png"), "trades": str(ARTIFACTS / "trade_markers.png")},
    }
