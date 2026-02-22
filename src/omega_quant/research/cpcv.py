from __future__ import annotations


def probability_of_backtest_overfitting(is_scores: list[float], oos_scores: list[float]) -> float | None:
    """CPCV/PBO is intentionally disabled until a full combinatorial purged CV is implemented."""
    _ = (is_scores, oos_scores)
    return None


def cpcv_gate(is_scores: list[float], oos_scores: list[float], max_pbo: float = 0.50) -> dict:
    _ = (is_scores, oos_scores, max_pbo)
    return {
        "pbo": None,
        "gate": "NOT_IMPLEMENTED",
        "label": "CPCV/PBO NOT IMPLEMENTED",
        "next_action": "Implement full combinatorial purged cross-validation before using this metric",
    }
