from __future__ import annotations


def factor_decomposition(strategy_returns: list[float], market_returns: list[float]) -> dict:
    """Simple single-factor beta/alpha decomposition proxy."""
    n = min(len(strategy_returns), len(market_returns))
    if n < 2:
        return {"alpha": 0.0, "beta": 0.0, "r2": 0.0}

    s = strategy_returns[:n]
    m = market_returns[:n]
    ms = sum(s) / n
    mm = sum(m) / n

    cov = sum((si - ms) * (mi - mm) for si, mi in zip(s, m)) / (n - 1)
    var_m = sum((mi - mm) ** 2 for mi in m) / (n - 1)
    beta = cov / var_m if var_m > 1e-12 else 0.0
    alpha = ms - beta * mm

    # r2 proxy from correlation^2
    var_s = sum((si - ms) ** 2 for si in s) / (n - 1)
    corr = cov / ((var_s * var_m) ** 0.5) if var_s > 1e-12 and var_m > 1e-12 else 0.0
    r2 = corr * corr

    return {"alpha": alpha, "beta": beta, "r2": r2}
