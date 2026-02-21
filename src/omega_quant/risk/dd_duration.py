from __future__ import annotations


def drawdown_duration(equity: list[float]) -> int:
    """Return bars since last equity peak (drawdown duration)."""
    if not equity:
        return 0
    peak = equity[0]
    duration = 0
    for v in equity:
        if v >= peak:
            peak = v
            duration = 0
        else:
            duration += 1
    return duration


def duration_escalation(duration_bars: int) -> str:
    if duration_bars > 60:
        return "FORCE_ORANGE"
    if duration_bars > 30:
        return "ESCALATE_ONE_LEVEL"
    return "NORMAL"
