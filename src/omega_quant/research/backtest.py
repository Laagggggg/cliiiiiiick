from __future__ import annotations


def run_simple_backtest(prices: list[float], entries: list[bool], exits: list[bool]) -> dict:
    position = 0
    entry_price = 0.0
    pnls: list[float] = []
    equity = [1.0]

    for p, ent, ex in zip(prices, entries, exits):
        if position == 0 and ent:
            position = 1
            entry_price = p
        elif position == 1 and ex:
            pnl = (p - entry_price) / entry_price
            pnls.append(pnl)
            equity.append(equity[-1] * (1 + pnl))
            position = 0

    total_return = equity[-1] - 1.0
    win_rate = (sum(1 for x in pnls if x > 0) / len(pnls)) if pnls else 0.0
    return {"trades": len(pnls), "total_return": total_return, "win_rate": win_rate, "equity": equity}
