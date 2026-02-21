from __future__ import annotations

import hashlib
import json
from pathlib import Path

from omega_quant.data.providers import get_provider_chain
from omega_quant.data.reconciler import reconcile_prices
from omega_quant.engine import run_step
from omega_quant.ops.logger import log_event
from omega_quant.ops.trade_review import render_trade_reviews_markdown
from omega_quant.paper_account.db import apply_fill, export_jsonl, get_account_summary, get_or_create_account, list_trades


ARTIFACTS = Path("artifacts")
DB_PATH = "artifacts/paper_account.sqlite3"


def _choose_bars(symbol: str = "SPY", timeframe: str = "1d", limit: int = 300) -> tuple[list[dict], str]:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars(symbol=symbol, timeframe=timeframe, limit=limit)
            rows = [
                {
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in bars
            ]
            if len(rows) >= 30:
                return rows, provider.source_name()
            errors.append(f"{provider.source_name()}:insufficient_bars")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")
    raise RuntimeError("no market data provider available: " + " | ".join(errors))


def _write_proof_markdown(path: str, result: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Paper Trading Proof Report",
        "",
        f"- Data Source: {result['data_source']}",
        f"- Starting Capital (session): ${result['starting_capital']:.2f}",
        f"- Ending Capital (session): ${result['ending_capital']:.2f}",
        f"- Session P&L: ${result['session_pnl_dollars']:.2f}",
        f"- Total Trades in Ledger: {result['ledger_trade_count']}",
        "",
        "## Session Trades",
        "| ID | Timestamp | Entry | Exit | Qty | PnL $ | Equity Before | Equity After |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for t in result["session_trades"]:
        lines.append(
            f"| {t['trade_id']} | {t['timestamp']} | {t['entry']:.4f} | {t['exit']:.4f} | {t['qty']:.4f} | {t['pnl_dollars']:.4f} | {t['equity_before']:.4f} | {t['equity_after']:.4f} |"
        )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_checksums(paths: list[Path], out_path: Path) -> None:
    lines: list[str] = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.as_posix()}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_paper_cycle(starting_capital: float = 5000.0, cycles: int = 1) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    account = get_or_create_account(starting_capital, db_path=DB_PATH)
    session_start = float(account["equity"])
    session_trade_start = len(list_trades(db_path=DB_PATH))

    rows, source = _choose_bars()
    closes_primary = [float(r["close"]) for r in rows]

    rec = {"passed": True, "degraded": True, "reason": "secondary_unavailable"}
    for provider in get_provider_chain():
        if provider.source_name() == source:
            continue
        try:
            secondary_rows = provider.get_bars(symbol="SPY", timeframe="1d", limit=len(rows))
            closes_secondary = [float(r.close) for r in secondary_rows][-len(closes_primary):]
            if len(closes_secondary) < 30:
                continue
            rec = reconcile_prices(closes_primary[-len(closes_secondary):], closes_secondary, tolerance_pct=0.25)
            rec["degraded"] = False
            break
        except Exception:  # noqa: BLE001
            continue

    if not rec["passed"]:
        return {"status": "HALT", "reason": "reconciliation_failed", "details": rec}

    for offset in range(max(1, cycles)):
        closes = closes_primary[: len(closes_primary) - max(0, cycles - 1 - offset)]
        decision = run_step(closes=closes, equity=float(get_account_summary(db_path=DB_PATH)["equity"]))
        if decision["status"] != "TRADE_FILLED":
            continue

        apply_fill(
            ts=rows[len(closes) - 1]["timestamp"],
            symbol="SPY",
            side="LONG",
            qty=decision["qty"],
            entry=decision["entry"],
            exit=decision["exit"],
            pnl_net=decision["pnl"],
            reason={
                "status": decision["status"],
                "reason": decision["reason"],
                "score": decision["score"],
                "threshold": decision["threshold"],
                "regime": decision["regime"],
                "data_source": source,
            },
            db_path=DB_PATH,
        )

    all_trades = list_trades(db_path=DB_PATH)
    session_trades = all_trades[session_trade_start:]
    ending = get_account_summary(db_path=DB_PATH)["equity"]
    result = {
        "status": "ok",
        "data_source": source,
        "starting_capital": session_start,
        "ending_capital": ending,
        "session_pnl_dollars": ending - session_start,
        "session_return_pct": ((ending - session_start) / session_start * 100.0) if session_start > 0 else 0.0,
        "session_trade_count": len(session_trades),
        "ledger_trade_count": len(all_trades),
        "session_trades": session_trades,
        "account_summary": get_account_summary(db_path=DB_PATH),
        "reconciliation": rec,
    }

    ledger_path = ARTIFACTS / "paper_ledger.json"
    ledger_path.write_text(json.dumps(all_trades, indent=2), encoding="utf-8")
    export_jsonl(path=str(ARTIFACTS / "paper_trades.jsonl"), db_path=DB_PATH)
    render_trade_reviews_markdown(str(ARTIFACTS / "paper_trades.jsonl"), str(ARTIFACTS / "paper_trade_reviews.md"))
    _write_proof_markdown(str(ARTIFACTS / "paper_proof_report.md"), result)
    (ARTIFACTS / "paper_cycle_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_checksums(
        [
            ARTIFACTS / "paper_cycle_result.json",
            ARTIFACTS / "paper_proof_report.md",
            ARTIFACTS / "paper_ledger.json",
            ARTIFACTS / "paper_trades.jsonl",
        ],
        ARTIFACTS / "checksums.sha256",
    )

    event = log_event("info", "paper_cycle", summary={k: result[k] for k in ["starting_capital", "ending_capital", "session_pnl_dollars", "session_return_pct", "session_trade_count"]})
    return {
        "result": result,
        "event": event,
        "review_file": str(ARTIFACTS / "paper_trade_reviews.md"),
        "proof_file": str(ARTIFACTS / "paper_proof_report.md"),
        "json_result": str(ARTIFACTS / "paper_cycle_result.json"),
        "ledger_file": str(ARTIFACTS / "paper_ledger.json"),
        "checksum_file": str(ARTIFACTS / "checksums.sha256"),
    }
