from __future__ import annotations


def circuit_breaker_level(drawdown_pct: float, duration_bars: int = 0) -> str:
    """
    GREEN:  DD < 5%
    YELLOW: DD 5-10%
    ORANGE: DD 10-15%
    RED:    DD > 15%

    Duration escalation:
      - duration > 60 bars => at least ORANGE
      - duration > 30 bars => escalate one level
    """
    if drawdown_pct > 0.15:
        base = "RED"
    elif drawdown_pct > 0.10:
        base = "ORANGE"
    elif drawdown_pct >= 0.05:
        base = "YELLOW"
    else:
        base = "GREEN"

    order = ["GREEN", "YELLOW", "ORANGE", "RED"]
    idx = order.index(base)

    if duration_bars > 60:
        idx = max(idx, order.index("ORANGE"))
    elif duration_bars > 30:
        idx = min(order.index("RED"), idx + 1)

    return order[idx]
