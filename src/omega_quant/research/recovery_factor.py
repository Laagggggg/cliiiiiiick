from __future__ import annotations


def recovery_factor(total_net_profit: float, max_drawdown: float) -> float:
    if max_drawdown == 0:
        return 0.0
    return abs(total_net_profit / max_drawdown)
