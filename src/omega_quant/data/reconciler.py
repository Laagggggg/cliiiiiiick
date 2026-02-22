from __future__ import annotations


def reconcile_prices(primary: list[float], secondary: list[float], tolerance_pct: float = 0.5) -> dict:
    """Compare two same-length close price streams; fail if any deviation > tolerance_pct."""
    if len(primary) != len(secondary) or not primary:
        return {"passed": False, "reason": "length_mismatch_or_empty", "max_diff_pct": None}

    diffs = []
    for p, s in zip(primary, secondary):
        if p <= 0 or s <= 0:
            return {"passed": False, "reason": "non_positive_price", "max_diff_pct": None}
        diffs.append(abs(p - s) / p * 100)

    max_diff = max(diffs)
    return {
        "passed": max_diff <= tolerance_pct,
        "reason": "ok" if max_diff <= tolerance_pct else "tolerance_breach",
        "max_diff_pct": max_diff,
    }
