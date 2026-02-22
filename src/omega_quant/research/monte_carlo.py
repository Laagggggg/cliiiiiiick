from __future__ import annotations

import random


def monte_carlo_sharpe(returns: list[float], paths: int = 200, seed: int = 42) -> dict:
    """Bootstrap-like MC using sampling with replacement and simple Sharpe proxy."""
    if not returns:
        return {"p5_sharpe": 0.0, "p95_sharpe": 0.0, "gate": "FAIL"}
    random.seed(seed)
    sharpes = []
    n = len(returns)
    for _ in range(max(10, paths)):
        sample = [returns[random.randrange(n)] for _ in range(n)]
        mu = sum(sample) / n
        var = sum((x - mu) ** 2 for x in sample) / max(1, n - 1)
        sd = var ** 0.5
        sharpe = mu / sd if sd > 1e-9 else 0.0
        sharpes.append(sharpe)
    sharpes.sort()
    p5 = sharpes[int(0.05 * (len(sharpes) - 1))]
    p95 = sharpes[int(0.95 * (len(sharpes) - 1))]
    return {"p5_sharpe": p5, "p95_sharpe": p95, "gate": "PASS" if p5 > 0 else "FAIL"}
