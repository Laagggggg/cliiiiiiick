from __future__ import annotations

from omega_quant.strategy.adaptive_threshold import adaptive_entry_threshold
from omega_quant.types import CompositeSignal


def compute_composite_signal(
    regime: str,
    regime_confidence: float,
    hurst_value: float,
    trend: float,
    reversion: float,
    quality_gate: float,
    macro_overlay: float,
    fractal_conf: float,
    htf_bias: str,
    adaptive_weights: dict[str, float],
) -> tuple[CompositeSignal, float]:
    if regime == "AVOID":
        return CompositeSignal(0.0, "FLAT", "AVOID"), 999.0

    if regime == "TRENDING":
        raw = adaptive_weights.get("trend", 0.7) * trend + adaptive_weights.get("reversion", 0.05) * reversion
    else:
        raw = adaptive_weights.get("trend", 0.1) * trend + adaptive_weights.get("reversion", 0.7) * reversion

    score = raw * quality_gate
    score *= 1.0 + fractal_conf * 0.10
    score *= macro_overlay

    if (htf_bias == "BULLISH" and score < 0) or (htf_bias == "BEARISH" and score > 0):
        score = 0.0

    threshold = adaptive_entry_threshold(regime, regime_confidence, hurst_value)
    direction = "LONG" if score > threshold else "FLAT"
    return CompositeSignal(score, direction, "OK"), threshold
