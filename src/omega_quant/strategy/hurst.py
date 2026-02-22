from __future__ import annotations

import math
from statistics import stdev

from omega_quant.types import Regime


def _rescaled_range(series: list[float]) -> float:
    """Compute R/S (rescaled range) for a segment — Mandelbrot & Wallis (1969)."""
    n = len(series)
    if n < 4:
        return 0.0
    mean_val = sum(series) / n
    deviations = [x - mean_val for x in series]
    cumulative: list[float] = []
    running = 0.0
    for d in deviations:
        running += d
        cumulative.append(running)
    r = max(cumulative) - min(cumulative)
    s = stdev(series) if n > 1 else 0.0
    if s < 1e-12:
        return 0.0
    return r / s


def _linreg_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    return num / den if den else 0.0


def hurst_exponent(series: list[float], max_lag: int = 20) -> float:
    """
    Hurst exponent via rescaled range (R/S) analysis.

    Regresses log(R/S) on log(window_size) across multiple non-overlapping
    window sizes.  Standard method from Mandelbrot & Wallis (1969).

    H > 0.5 => trending / persistent
    H = 0.5 => random walk
    H < 0.5 => mean-reverting / anti-persistent
    """
    clean = [float(x) for x in series if x is not None]
    if len(clean) < max_lag + 5:
        return 0.5

    # Use returns (first differences) for R/S analysis
    returns = [clean[i] - clean[i - 1] for i in range(1, len(clean))]
    if len(returns) < 10:
        return 0.5

    min_window = 4
    log_ns: list[float] = []
    log_rs: list[float] = []

    # Generate window sizes: powers of 2 and half-powers for granularity
    windows = sorted(set(
        [min_window]
        + [int(min_window * (2 ** (i / 2))) for i in range(1, 20)]
    ))
    windows = [w for w in windows if min_window <= w <= len(returns)]

    for window in windows:
        n_segments = len(returns) // window
        if n_segments < 1:
            continue
        rs_values: list[float] = []
        for seg in range(n_segments):
            segment = returns[seg * window : (seg + 1) * window]
            rs = _rescaled_range(segment)
            if rs > 0:
                rs_values.append(rs)
        if rs_values:
            avg_rs = sum(rs_values) / len(rs_values)
            if avg_rs > 0:
                log_ns.append(math.log(window))
                log_rs.append(math.log(avg_rs))

    if len(log_ns) < 3:
        return 0.5

    slope = _linreg_slope(log_ns, log_rs)
    return min(1.0, max(0.0, slope))


def hurst_regime(h: float, trend_thresh: float = 0.55, revert_thresh: float = 0.45) -> Regime:
    if h > trend_thresh:
        return Regime.TRENDING
    if h < revert_thresh:
        return Regime.RANGING
    return Regime.NEUTRAL
