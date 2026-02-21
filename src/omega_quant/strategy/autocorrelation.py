from __future__ import annotations

from omega_quant.types import Regime


def _autocorr(values: list[float], lag: int) -> float:
    if len(values) <= lag + 2:
        return 0.0
    x = values[:-lag]
    y = values[lag:]
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = sum((a - mx) ** 2 for a in x)
    deny = sum((b - my) ** 2 for b in y)
    den = (denx * deny) ** 0.5
    return num / den if den else 0.0


def autocorrelation_regime(returns: list[float], lags: list[int] | None = None) -> tuple[Regime, float]:
    lags = lags or [1, 5, 10, 20]
    acf = [_autocorr(returns, l) for l in lags]
    short = sum(acf[:2]) / 2
    if short > 0.05:
        return Regime.TRENDING, short
    if short < -0.05:
        return Regime.RANGING, short
    return Regime.NEUTRAL, short
