from __future__ import annotations

from collections import Counter


from omega_quant.types import Regime


WEIGHTS = {
    "adx": 1.0,
    "vol": 1.0,
    "ma": 1.0,
    "hmm": 1.0,
    "hurst": 2.0,
    "autocorr": 1.5,
}


def classify_regime(votes: dict[str, Regime], hurst_value: float) -> tuple[Regime, float]:
    if Regime.AVOID in votes.values():
        return Regime.AVOID, 1.0

    score = 0.0
    for method, vote in votes.items():
        w = WEIGHTS.get(method, 1.0)
        if vote == Regime.TRENDING:
            score += w
        elif vote == Regime.RANGING:
            score -= w

    norm = score / sum(WEIGHTS.values())
    if -0.20 <= norm <= 0.20:
        regime = Regime.RANGING
        conf = 0.3
    else:
        regime = Regime.TRENDING if norm > 0 else Regime.RANGING
        conf = abs(norm)

    if 0.45 <= hurst_value <= 0.55:
        conf = min(conf, 0.5)
    return regime, float(conf)


def majority_vote(votes: list[Regime]) -> Regime:
    if not votes:
        return Regime.NEUTRAL
    return Counter(votes).most_common(1)[0][0]
