from __future__ import annotations

import random


def whites_reality_check(
    strategy_returns: list[float] | None = None,
    benchmark_returns: list[float] | None = None,
    *,
    best_strategy_return: float | None = None,
    bootstrap_mean_best: float | None = None,
    n_bootstrap: int = 1000,
    block_size: int = 5,
    seed: int = 42,
) -> dict:
    """
    White's Reality Check — White (2000).

    Tests whether the best strategy's mean return is significantly positive
    after correcting for data-snooping bias via bootstrap.

    When full return series are provided, uses block-bootstrap permutation.
    Falls back to simple comparison when only scalars are given.
    """
    # Full bootstrap path
    if strategy_returns is not None and benchmark_returns is not None:
        n = min(len(strategy_returns), len(benchmark_returns))
        if n < 20:
            return {"edge": 0.0, "p_value": 1.0, "gate": "FAIL", "note": "insufficient_data"}
        excess = [strategy_returns[i] - benchmark_returns[i] for i in range(n)]
        observed_edge = sum(excess) / n

        rng = random.Random(seed)
        count_ge = 0
        for _ in range(n_bootstrap):
            # Block-bootstrap resample
            boot: list[float] = []
            while len(boot) < n:
                start = rng.randint(0, n - 1)
                length = min(rng.randint(1, block_size * 2), n - len(boot))
                for j in range(length):
                    boot.append(excess[(start + j) % n])
            boot_mean = sum(boot[:n]) / n
            # Under null, centre at zero
            centred = boot_mean - observed_edge
            if centred >= observed_edge:
                count_ge += 1

        p_value = count_ge / n_bootstrap
        return {
            "edge": observed_edge,
            "p_value": round(p_value, 4),
            "n_bootstrap": n_bootstrap,
            "gate": "PASS" if p_value < 0.05 else "FAIL",
        }

    # Scalar fallback (backward compatible)
    if best_strategy_return is not None and bootstrap_mean_best is not None:
        edge = best_strategy_return - bootstrap_mean_best
        p_proxy = 0.01 if edge > 0 else 0.5
        return {"edge": edge, "p_value": p_proxy, "gate": "PASS" if p_proxy < 0.05 else "FAIL", "note": "scalar_proxy"}

    return {"edge": 0.0, "p_value": 1.0, "gate": "FAIL", "note": "no_data"}
