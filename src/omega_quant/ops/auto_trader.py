from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradeRecord:
    trade_id: int
    side: str
    entry_price: float
    exit_price: float
    units: float
    pnl_dollars: float
    pnl_pct_on_trade: float
    equity_before: float
    equity_after: float
    equity_growth_dollars: float
    equity_growth_pct: float


def run_auto_trader(prices: list[float], starting_capital: float, risk_fraction: float = 0.20) -> dict:
    if starting_capital <= 0:
        raise ValueError("starting_capital must be > 0")
    if len(prices) < 6:
        raise ValueError("need at least 6 prices")

    equity = starting_capital
    trades: list[TradeRecord] = []
    trade_id = 1

    # deterministic auto-trader: if 3-bar momentum positive, long next bar and exit one bar later
    for i in range(3, len(prices) - 1):
        momentum = prices[i] - prices[i - 3]
        if momentum <= 0:
            continue

        entry = prices[i]
        exit_ = prices[i + 1]
        alloc = equity * risk_fraction
        units = alloc / entry if entry > 0 else 0.0
        if units <= 0:
            continue

        pnl = (exit_ - entry) * units
        before = equity
        after = equity + pnl
        growth_d = after - before
        growth_pct = (growth_d / before * 100.0) if before > 0 else 0.0
        trade_pct = ((exit_ - entry) / entry * 100.0) if entry > 0 else 0.0

        trades.append(
            TradeRecord(
                trade_id=trade_id,
                side="LONG",
                entry_price=entry,
                exit_price=exit_,
                units=units,
                pnl_dollars=pnl,
                pnl_pct_on_trade=trade_pct,
                equity_before=before,
                equity_after=after,
                equity_growth_dollars=growth_d,
                equity_growth_pct=growth_pct,
            )
        )

        equity = after
        trade_id += 1

    wins = sum(1 for t in trades if t.pnl_dollars > 0)
    losses = sum(1 for t in trades if t.pnl_dollars <= 0)
    total_pnl = equity - starting_capital
    total_return_pct = (total_pnl / starting_capital * 100.0) if starting_capital > 0 else 0.0

    avg_win = (sum(t.pnl_dollars for t in trades if t.pnl_dollars > 0) / wins) if wins else 0.0
    avg_loss = (abs(sum(t.pnl_dollars for t in trades if t.pnl_dollars <= 0)) / losses) if losses else 0.0
    win_rate = (wins / len(trades) * 100.0) if trades else 0.0
    expectancy = ((win_rate / 100.0) * avg_win) - ((1 - win_rate / 100.0) * avg_loss) if trades else 0.0

    return {
        "starting_capital": starting_capital,
        "ending_capital": equity,
        "total_pnl_dollars": total_pnl,
        "total_return_pct": total_return_pct,
        "trade_count": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": win_rate,
        "avg_win_dollars": avg_win,
        "avg_loss_dollars": avg_loss,
        "expectancy_dollars": expectancy,
        "trades": [t.__dict__ for t in trades],
    }
