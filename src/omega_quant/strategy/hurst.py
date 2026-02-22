from __future__ import annotations

import math
from statistics import pstdev

from omega_quant.types import Regime


def _diff(values: list[float], lag: int) -> list[float]:
    return [values[i] - values[i - lag] for i in range(lag, len(values))]


def _linreg_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    return num / den if den else 0.0


def hurst_exponent(series: list[float], max_lag: int = 20) -> float:
    clean = [float(x) for x in series if x is not None]
    if len(clean) < max_lag + 5:
        return 0.5
    lags = list(range(2, max_lag))
    taus: list[float] = []
    valid_lags: list[int] = []
    for lag in lags:
        d = _diff(clean, lag)
        sd = pstdev(d) if len(d) > 1 else 0.0
        if sd > 0:
            valid_lags.append(lag)
            taus.append(sd)
    if len(taus) < 3:
        return 0.5
    slope = _linreg_slope([math.log(x) for x in valid_lags], [math.log(y) for y in taus])
    return min(1.0, max(0.0, slope))


def hurst_regime(h: float, trend_thresh: float = 0.55, revert_thresh: float = 0.45) -> Regime:
    if h > trend_thresh:
        return Regime.TRENDING
    if h < revert_thresh:
        return Regime.RANGING
    return Regime.NEUTRAL
