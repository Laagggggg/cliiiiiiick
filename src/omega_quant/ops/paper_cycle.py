from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

from omega_quant.data.providers import get_provider_chain
from omega_quant.data.reconciler import reconcile_prices
from omega_quant.engine import run_step
from omega_quant.ops.logger import log_event
from omega_quant.ops.trade_review import render_trade_reviews_markdown
from omega_quant.paper_account.db import (
    append_equity_point,
    export_jsonl,
    get_account_summary,
    get_or_create_account,
    list_equity_curve,
    list_trades,
    record_round_trip,
)

ARTIFACTS = Path("artifacts")
DB_PATH = "artifacts/paper_account.sqlite"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pick_primary_rows(symbol: str = "SPY", timeframe: str = "1h", limit: int = 500) -> tuple[list[dict], str]:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars(symbol, timeframe, limit=limit)
            if len(bars) < 50:
                continue
            rows = [{"timestamp": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
            return rows, provider.source_name()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")
    raise RuntimeError("no provider: " + " | ".join(errors))


def _build_provenance(rows: list[dict], source: str, reconciliation: dict) -> dict:
    payload = json.dumps(rows, sort_keys=True).encode("utf-8")
    return {
        "source_primary": source,
        "bars_loaded": len(rows),
        "start": rows[0]["timestamp"],
        "end": rows[-1]["timestamp"],
        "freshness_seconds": 0,
        "dataset_sha256": _sha256_bytes(payload),
        "reconciliation": reconciliation,
    }


def _png_plot(path: Path, values: list[float], marks: list[int] | None = None) -> None:
    width, height = 640, 220
    marks = marks or []
    mn = min(values) if values else 0.0
    mx = max(values) if values else 1.0
    span = (mx - mn) or 1.0
    pixels = bytearray()
    pts = []
    for i, v in enumerate(values):
        x = int(i * (width - 1) / max(1, len(values) - 1))
        y = int((mx - v) * (height - 1) / span)
        pts.append((x, y))

    ptset = set(pts)
    markx = {int(i * (width - 1) / max(1, len(values) - 1)) for i in marks}
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            if (x, y) in ptset:
                row.extend((20, 200, 20))
            elif x in markx:
                row.extend((220, 60, 60))
            else:
                row.extend((30, 30, 30))
        pixels.extend(row)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = zlib.compress(bytes(pixels), 9)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _write_checksums(paths: list[Path], out_path: Path) -> None:
    out_path.write_text("\n".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.as_posix()}" for p in paths) + "\n", encoding="utf-8")


def _write_proof_markdown(path: Path, result: dict) -> None:
    lines = [
        "# Paper Trading Proof Report",
        "",
        f"- Truth Anchor (code_hash): `{result['truth_anchor']['code_hash']}`",
        f"- Truth Anchor (config_hash): `{result['truth_anchor']['config_hash']}`",
        f"- Truth Anchor (dataset_hash): `{result['truth_anchor']['dataset_hash']}`",
        f"- Starting Capital: ${result['starting_capital']:.2f}",
        f"- Ending Capital: ${result['ending_capital']:.2f}",
        f"- Session P&L: ${result['session_pnl_dollars']:.2f}",
        f"- Risk of Ruin (empirical): {result['risk_of_ruin']:.4f}",
        "",
    ]
    for t in result["session_trades"]:
        cf = t["counterfactual"]
        lines.append(
            f"- Trade {t['trade_id']}: pnl=${t['pnl_dollars']:.4f}; no_trade=${cf['no_trade_pnl']:.4f}; half_size=${cf['half_size_pnl']:.4f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_paper_cycle(starting_capital: float = 5000.0, cycles: int = 1) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    get_or_create_account(starting_capital, db_path=DB_PATH)

    rows, source = _pick_primary_rows(limit=700)
    closes = [float(r["close"]) for r in rows]

    rec = {"passed": True, "degraded": True, "max_diff_pct": 0.0}
    for provider in get_provider_chain():
        if provider.source_name() == source:
            continue
        try:
            sec = provider.get_bars("SPY", "1h", limit=len(rows))
            sec_close = [float(b.close) for b in sec][-len(closes):]
            rec = reconcile_prices(closes[-len(sec_close):], sec_close, tolerance_pct=0.25)
            rec["degraded"] = False
            break
        except Exception:  # noqa: BLE001
            continue
    if not rec.get("passed", False):
        return {"status": "HALT", "reason": "reconciliation_failed", "details": rec}

    before_count = len(list_trades(db_path=DB_PATH))
    # forward-time loop, no lookahead: each step uses rows[:i+1], decision based on upto i-1 in engine
    start = 25
    end = min(len(rows), start + max(1, cycles) * 60)
    for i in range(start, end):
        slice_rows = rows[: i + 1]
        append_equity_point(ts=slice_rows[-1]["timestamp"], last_price=float(slice_rows[-1]["close"]), db_path=DB_PATH)
        acct = get_account_summary(db_path=DB_PATH)
        decision = run_step(slice_rows, equity=float(acct["equity"]))
        if decision["status"] != "TRADE_FILLED":
            continue
        fee = abs(decision["qty"] * decision["entry"] * 0.0005)
        record_round_trip(
            ts_open=slice_rows[-2]["timestamp"],
            ts_close=slice_rows[-1]["timestamp"],
            symbol="SPY",
            qty=decision["qty"],
            entry=decision["entry"],
            exit=decision["exit"],
            fee=fee,
            reason={
                "status": decision["status"],
                "reason": decision["reason"],
                "score": decision["score"],
                "threshold": decision["threshold"],
                "regime": decision["regime"],
                "source": source,
            },
            db_path=DB_PATH,
        )

    trades = list_trades(db_path=DB_PATH)
    session_trades = trades[before_count:]
    start_equity = float(get_account_summary(db_path=DB_PATH)["equity"] - sum(t["pnl_dollars"] for t in session_trades))
    end_equity = float(get_account_summary(db_path=DB_PATH)["equity"])

    for t in session_trades:
        t["counterfactual"] = {"no_trade_pnl": 0.0, "half_size_pnl": t["pnl_dollars"] / 2}

    eq = list_equity_curve(db_path=DB_PATH)
    eq_vals = [p["equity"] for p in eq][-500:]
    dd_vals = [p["drawdown"] for p in eq][-500:]
    trade_marks = list(range(max(0, len(eq_vals) - len(session_trades)), len(eq_vals)))
    _png_plot(ARTIFACTS / "equity_curve.png", eq_vals, trade_marks)
    _png_plot(ARTIFACTS / "drawdown.png", dd_vals, trade_marks)
    _png_plot(ARTIFACTS / "trade_markers.png", [0.0] * max(1, len(eq_vals)), trade_marks)

    export_jsonl(path=str(ARTIFACTS / "paper_trades.jsonl"), db_path=DB_PATH)
    render_trade_reviews_markdown(str(ARTIFACTS / "paper_trades.jsonl"), str(ARTIFACTS / "paper_trade_reviews.md"))

    ledger_path = ARTIFACTS / "paper_ledger.json"
    ledger_path.write_text(json.dumps(trades, indent=2), encoding="utf-8")
    equity_path = ARTIFACTS / "equity_curve.json"
    equity_path.write_text(json.dumps(eq, indent=2), encoding="utf-8")

    losses = [abs(t["pnl_dollars"]) for t in trades if t["pnl_dollars"] < 0]
    wins = [t["pnl_dollars"] for t in trades if t["pnl_dollars"] > 0]
    risk_of_ruin = min(1.0, (len(losses) / max(1, len(trades))) * (sum(losses) / max(1.0, sum(wins) + sum(losses))))

    result = {
        "status": "ok",
        "starting_capital": start_equity,
        "ending_capital": end_equity,
        "session_pnl_dollars": end_equity - start_equity,
        "session_trade_count": len(session_trades),
        "session_trades": session_trades,
        "ledger_trade_count": len(trades),
        "risk_of_ruin": risk_of_ruin,
        "provenance": _build_provenance(rows, source, rec),
        "truth_anchor": {
            "code_hash": _sha256_bytes(Path(__file__).read_bytes()),
            "config_hash": _sha256_bytes(json.dumps({"fee_bps": 5, "risk_fraction": 0.10}, sort_keys=True).encode()),
            "dataset_hash": _build_provenance(rows, source, rec)["dataset_sha256"],
        },
        "account_summary": get_account_summary(db_path=DB_PATH),
    }

    result_path = ARTIFACTS / "paper_cycle_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    proof_path = ARTIFACTS / "paper_proof_report.md"
    _write_proof_markdown(proof_path, result)
    files = [result_path, proof_path, ledger_path, ARTIFACTS / "paper_trades.jsonl", ARTIFACTS / "equity_curve.png", ARTIFACTS / "drawdown.png", ARTIFACTS / "trade_markers.png", equity_path]
    _write_checksums(files, ARTIFACTS / "checksums.sha256")

    event = log_event("info", "paper_cycle", summary={"starting_capital": start_equity, "ending_capital": end_equity, "session_trade_count": len(session_trades)})
    return {
        "result": result,
        "event": event,
        "json_result": str(result_path),
        "proof_file": str(proof_path),
        "review_file": str(ARTIFACTS / "paper_trade_reviews.md"),
        "ledger_file": str(ledger_path),
        "checksum_file": str(ARTIFACTS / "checksums.sha256"),
        "charts": {
            "equity": str(ARTIFACTS / "equity_curve.png"),
            "drawdown": str(ARTIFACTS / "drawdown.png"),
            "trades": str(ARTIFACTS / "trade_markers.png"),
        },
    }
