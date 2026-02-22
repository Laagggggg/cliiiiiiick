from __future__ import annotations


def run_simple_backtest(prices: list[float], entries: list[bool], exits: list[bool]) -> dict:
    """
    Simple backtest with strict no-lookahead enforcement.

    Signals at bar i are generated from data up to bar i.
    Execution occurs at bar i+1 open (approximated by next bar's price).
    This 1-bar delay is the minimum realistic latency.
    """
    position = 0
    entry_price = 0.0
    pnls: list[float] = []
    equity = [1.0]

    n = len(prices)
    for i in range(n):
        if position == 0 and entries[i]:
            # Signal fires at bar i; fill at bar i+1 price
            if i + 1 < n:
                position = 1
                entry_price = prices[i + 1]
        elif position == 1 and exits[i]:
            # Exit signal at bar i; fill at bar i+1 price
            if i + 1 < n:
                exit_price = prices[i + 1]
                pnl = (exit_price - entry_price) / entry_price
                pnls.append(pnl)
                equity.append(equity[-1] * (1 + pnl))
                position = 0

    total_return = equity[-1] - 1.0
    win_rate = (sum(1 for x in pnls if x > 0) / len(pnls)) if pnls else 0.0
    return {"trades": len(pnls), "total_return": total_return, "win_rate": win_rate, "equity": equity}
