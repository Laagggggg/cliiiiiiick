from __future__ import annotations


def _corr(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = sum((a - mx) ** 2 for a in x)
    deny = sum((b - my) ** 2 for b in y)
    den = (denx * deny) ** 0.5
    return num / den if den else 0.0


def correlation_guard(series_a: list[float], series_b: list[float], threshold: float = 0.40) -> dict:
    c = _corr(series_a, series_b)
    return {
        "corr": c,
        "passed": abs(c) < threshold,
        "action": "reduce_weight" if abs(c) >= threshold else "ok",
    }
