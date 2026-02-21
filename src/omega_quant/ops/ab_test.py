from __future__ import annotations


def choose_variant(trade_id: str, weight_a: float = 0.5) -> str:
    """Deterministic A/B split by trade_id hash."""
    h = sum(ord(ch) for ch in trade_id) % 1000
    return "A" if (h / 1000.0) < weight_a else "B"


def compare_variants(metrics_a: dict, metrics_b: dict) -> dict:
    sharpe_a = float(metrics_a.get("sharpe", 0.0))
    sharpe_b = float(metrics_b.get("sharpe", 0.0))
    dd_a = float(metrics_a.get("max_dd", 1.0))
    dd_b = float(metrics_b.get("max_dd", 1.0))

    score_a = sharpe_a - dd_a
    score_b = sharpe_b - dd_b
    winner = "A" if score_a >= score_b else "B"
    return {"winner": winner, "score_a": score_a, "score_b": score_b}
