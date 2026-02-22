from __future__ import annotations


def adaptive_entry_threshold(regime: str, regime_confidence: float, hurst_value: float) -> float:
    base = {"TRENDING": 0.45, "RANGING": 0.50, "AVOID": 999.0}.get(regime, 0.55)
    # Penalise random-walk zone (H~0.5): raise threshold when Hurst is near 0.5
    # Reward strong H signals (far from 0.5): lower threshold when confidence is high
    hurst_distance = abs(hurst_value - 0.5)
    hurst_penalty = max(0.0, 0.10 * (1.0 - hurst_distance * 4.0))  # max penalty when H=0.5
    confidence_bonus = (regime_confidence - 0.5) * 0.10
    return max(0.35, min(0.65, base + hurst_penalty - confidence_bonus))
