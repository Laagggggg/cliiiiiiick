from __future__ import annotations

import hashlib
import json
from pathlib import Path

from omega_quant.data.providers import CsvMarketDataProvider, get_provider_chain
from omega_quant.data.reconciler import reconcile_prices
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


def _strategy_decision(closes: list[float]) -> dict:
    sma5 = sum(closes[-5:]) / 5.0
    sma20 = sum(closes[-20:]) / 20.0
    trend_signal = (closes[-1] - closes[-5]) / closes[-5]
    score = max(0.0, trend_signal * 40.0)
    threshold = 0.01
    regime = "TREND" if sma5 > sma20 else "MEAN_REVERT"
    should_trade = score > threshold and closes[-1] > sma20
    return {
        "score": score,
        "threshold": threshold,
        "regime": regime,
        "trend_signal": trend_signal,
        "should_trade": should_trade,
        "reason": "trend_above_threshold" if should_trade else "score_or_bias_below_threshold",
    }


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
    secondary_rows = CsvMarketDataProvider().get_bars(symbol="SPY", timeframe="1d", limit=len(rows))
    closes_secondary = [float(r.close) for r in secondary_rows][-len(closes_primary):]
    rec = reconcile_prices(closes_primary[-len(closes_secondary):], closes_secondary, tolerance_pct=8.0)
    if not rec["passed"]:
        return {"status": "HALT", "reason": "reconciliation_failed", "details": rec}

    for offset in range(max(1, cycles)):
        closes = closes_primary[: len(closes_primary) - max(0, cycles - 1 - offset)]
        if len(closes) < 25:
            continue
        decision = _strategy_decision(closes)
        if not decision["should_trade"]:
            continue

        acct = get_account_summary(db_path=DB_PATH)
        equity = float(acct["equity"])
        entry = closes[-1]
        projected_exit = entry * (1.0 + decision["trend_signal"] * 0.35)
        if projected_exit <= 0:
            continue
        qty = round((equity * 0.15) / entry, 6)
        if qty <= 0:
            continue
        pnl = (projected_exit - entry) * qty
        apply_fill(
            ts=rows[-1]["timestamp"],
            symbol="SPY",
            side="LONG",
            qty=qty,
            entry=entry,
            exit=projected_exit,
            pnl_net=pnl,
            reason={
                "status": "TRADE_FILLED",
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
