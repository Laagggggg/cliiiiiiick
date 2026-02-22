from __future__ import annotations

from omega_quant.types import Trade


def _percentile(values: list[float], pct: int) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * (pct / 100)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1 - frac) + s[hi] * frac


class MAEOptimizedStops:
    def __init__(self, min_sample: int = 50, percentile: int = 80) -> None:
        self.min_sample = min_sample
        self.percentile = percentile

    def compute_optimal_stop(self, historical_trades: list[Trade]) -> float:
        winners = [t for t in historical_trades if t.pnl > 0]
        if len(winners) < self.min_sample:
            return 2.0
        return _percentile([t.max_adverse_excursion for t in winners], self.percentile)

    def compute_optimal_target(self, historical_trades: list[Trade], percentile: int = 50) -> float:
        winners = [t for t in historical_trades if t.pnl > 0]
        if len(winners) < self.min_sample:
            return 3.0
        return _percentile([t.max_favorable_excursion for t in winners], percentile)
