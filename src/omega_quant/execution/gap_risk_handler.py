from __future__ import annotations

from datetime import datetime


def assess_gap_risk(time_of_day: str, vix: float, earnings_tomorrow: bool, now: datetime | None = None) -> tuple[str, int]:
    risk = 0
    if time_of_day > "15:30":
        risk += 2
    if vix > 25:
        risk += 3
    if earnings_tomorrow:
        risk += 4
    ref = now or datetime.utcnow()
    if ref.weekday() == 4:
        risk += 1

    if risk >= 6:
        return "HIGH", risk
    if risk >= 4:
        return "MODERATE", risk
    return "LOW", risk
