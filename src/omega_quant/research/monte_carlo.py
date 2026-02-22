from __future__ import annotations

import random


def _sharpe(sample: list[float]) -> float:
    n = len(sample)
    if n < 2:
        return 0.0
    mu = sum(sample) / n
    var = sum((x - mu) ** 2 for x in sample) / max(1, n - 1)
    sd = var ** 0.5
    return mu / sd if sd > 1e-9 else 0.0


def _block_sample(returns: list[float], block_size: int, rng: random.Random) -> list[float]:
    n = len(returns)
    if n <= 1:
        return returns[:]
    b = max(2, min(block_size, n))
    out: list[float] = []
    while len(out) < n:
        start = rng.randrange(0, max(1, n - b + 1))
        out.extend(returns[start : start + b])
    return out[:n]


def monte_carlo_sharpe(returns: list[float], paths: int = 200, seed: int = 42, method: str = "block", block_size: int = 8) -> dict:
    if not returns:
        return {"p5_sharpe": 0.0, "p95_sharpe": 0.0, "gate": "FAIL", "method": "NONE"}
    rng = random.Random(seed)
    sharpes = []
    n_paths = max(10, paths)
    method_key = method.upper()
    for _ in range(n_paths):
        if method_key == "LEGACY_IID":
            sample = [returns[rng.randrange(len(returns))] for _ in range(len(returns))]
        else:
            sample = _block_sample(returns, block_size=block_size, rng=rng)
            method_key = "BLOCK_BOOTSTRAP"
        sharpes.append(_sharpe(sample))
    sharpes.sort()
    p5 = sharpes[int(0.05 * (len(sharpes) - 1))]
    p95 = sharpes[int(0.95 * (len(sharpes) - 1))]
    return {"p5_sharpe": p5, "p95_sharpe": p95, "gate": "PASS" if p5 > 0 else "FAIL", "method": method_key, "block_size": block_size}
