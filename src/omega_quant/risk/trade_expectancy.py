from __future__ import annotations

from statistics import mean

from omega_quant.types import Trade


def compute_trade_expectancy(recent_trades: list[Trade], window: int = 50) -> dict:
    sample = recent_trades[-window:]
    if not sample:
        return {"expectancy": 0.0, "gate": "FAIL"}
    wins = [t.pnl for t in sample if t.pnl > 0]
    losses = [abs(t.pnl) for t in sample if t.pnl <= 0]
    win_rate = len(wins) / len(sample)
    avg_win = mean(wins) if wins else 0.0
    avg_loss = mean(losses) if losses else 1.0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    payoff = avg_win / avg_loss if avg_loss > 0 else 0.0
    kelly = (win_rate * payoff - (1 - win_rate)) / payoff if payoff > 0 else 0.0
    return {
        "expectancy": expectancy,
        "win_rate": win_rate,
        "payoff_ratio": payoff,
        "kelly_optimal_pct": kelly,
        "kelly_quarter_pct": kelly * 0.25,
        "gate": "PASS" if expectancy > 0 else "FAIL",
    }
