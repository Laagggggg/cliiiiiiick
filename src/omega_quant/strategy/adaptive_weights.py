from __future__ import annotations


def compute_adaptive_weights(regime: str, family_sharpes: dict[str, float], min_weight: float = 0.05) -> dict[str, float]:
    active = ["trend", "reversion"] if regime in {"TRENDING", "RANGING"} else ["trend", "reversion"]
    sharpes = {f: max(0.0, family_sharpes.get(f, 0.0)) for f in active}
    total = sum(sharpes.values())
    if total == 0:
        return {f: 1 / len(active) for f in active}
    weights = {f: max(min_weight, s / total) for f, s in sharpes.items()}
    renorm = sum(weights.values())
    return {f: w / renorm for f, w in weights.items()}
