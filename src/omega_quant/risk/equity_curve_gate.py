from __future__ import annotations

from statistics import mean, pstdev


def equity_curve_gate(equity_series: list[float], lookback: int = 50) -> str:
    if len(equity_series) < lookback:
        return "NORMAL"
    window = equity_series[-lookback:]
    m = mean(window)
    s = pstdev(window) if len(window) > 1 else 0.0
    cur = equity_series[-1]
    if cur < m - 2 * s:
        return "HALT"
    if cur < m - s:
        return "REDUCE_50"
    return "NORMAL"
