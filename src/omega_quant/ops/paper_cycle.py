from __future__ import annotations

from pathlib import Path
import json

from omega_quant.ops.auto_trader import run_auto_trader
from omega_quant.ops.logger import log_event
from omega_quant.ops.trade_review import append_trade_review, render_trade_reviews_markdown


def sample_prices(cycles: int) -> list[float]:
    base = [100, 101, 102, 103, 102, 104, 106, 105, 107, 109, 108, 111]
    out = []
    for c in range(max(1, cycles)):
        shift = c * 0.5
        out.extend([p + shift for p in base])
    return out


def _write_proof_markdown(path: str, result: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Paper Trading Proof Report",
        "",
        f"- Starting Capital: ${result['starting_capital']:.2f}",
        f"- Ending Capital: ${result['ending_capital']:.2f}",
        f"- Total P&L: ${result['total_pnl_dollars']:.2f}",
        f"- Total Return: {result['total_return_pct']:.2f}%",
        f"- Trades: {result['trade_count']} (wins: {result['wins']}, losses: {result['losses']})",
        f"- Win Rate: {result['win_rate_pct']:.2f}%",
        f"- Expectancy per trade: ${result['expectancy_dollars']:.4f}",
        "",
        "## Per-Trade Growth Evidence",
        "| ID | Entry | Exit | PnL $ | Trade % | Equity Before | Equity After | Equity Growth $ | Equity Growth % |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for t in result["trades"]:
        lines.append(
            f"| {t['trade_id']} | {t['entry_price']:.4f} | {t['exit_price']:.4f} | {t['pnl_dollars']:.4f} | {t['pnl_pct_on_trade']:.4f}% | {t['equity_before']:.4f} | {t['equity_after']:.4f} | {t['equity_growth_dollars']:.4f} | {t['equity_growth_pct']:.4f}% |"
        )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_paper_cycle(starting_capital: float = 5000.0, cycles: int = 1) -> dict:
    prices = sample_prices(cycles)
    result = run_auto_trader(prices=prices, starting_capital=starting_capital)

    for t in result["trades"]:
        append_trade_review(
            "artifacts/paper_trades.jsonl",
            {
                "status": "TRADE" if t["pnl_dollars"] > 0 else "LOSS_TRADE",
                "score": round(t["pnl_pct_on_trade"], 6),
                "threshold": "n/a",
                "reason": "auto_trader_momentum_entry",
                "pnl_dollars": round(t["pnl_dollars"], 6),
                "equity_growth_pct": round(t["equity_growth_pct"], 6),
            },
        )

    render_trade_reviews_markdown("artifacts/paper_trades.jsonl", "artifacts/paper_trade_reviews.md")
    _write_proof_markdown("artifacts/paper_proof_report.md", result)
    Path("artifacts/paper_cycle_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    event = log_event("info", "paper_cycle", summary={k: result[k] for k in ["starting_capital", "ending_capital", "total_pnl_dollars", "total_return_pct", "trade_count"]})
    return {
        "result": result,
        "event": event,
        "review_file": str(Path("artifacts/paper_trade_reviews.md")),
        "proof_file": str(Path("artifacts/paper_proof_report.md")),
        "json_result": str(Path("artifacts/paper_cycle_result.json")),
    }
