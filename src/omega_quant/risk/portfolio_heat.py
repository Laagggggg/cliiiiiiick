from __future__ import annotations

from omega_quant.types import Position


def calculate_portfolio_heat(open_positions: list[Position], capital: float) -> float:
    if capital <= 0:
        return 1.0
    total_risk = sum(p.shares * abs(p.current_price - p.stop_price) for p in open_positions)
    return total_risk / capital
