from __future__ import annotations


def sentiment_overlay(put_call_ratio: float, breadth_above_200ma_pct: float) -> float:
    """Return conservative multiplier in [0.2, 1.1]."""
    mult = 1.0

    # extreme fear can be contrarian-positive, extreme complacency negative
    if put_call_ratio > 1.2:
        mult += 0.05
    elif put_call_ratio < 0.7:
        mult -= 0.10

    # weak breadth reduces confidence
    if breadth_above_200ma_pct < 30:
        mult -= 0.25
    elif breadth_above_200ma_pct > 65:
        mult += 0.05

    return max(0.2, min(1.1, mult))
