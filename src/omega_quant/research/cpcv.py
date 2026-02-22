from __future__ import annotations


def probability_of_backtest_overfitting(is_scores: list[float], oos_scores: list[float]) -> float:
    """
    Lightweight PBO proxy:
    fraction of folds where rank relation between IS and OOS degrades materially.
    """
    n = min(len(is_scores), len(oos_scores))
    if n == 0:
        return 1.0

    # sort by IS descending, inspect OOS median split consistency
    idx = sorted(range(n), key=lambda i: is_scores[i], reverse=True)
    half = max(1, n // 2)
    top = idx[:half]
    bot = idx[half:]

    top_oos = sum(oos_scores[i] for i in top) / len(top)
    bot_oos = sum(oos_scores[i] for i in bot) / len(bot) if bot else top_oos

    # if top IS underperforms bottom IS in OOS, indicates overfit
    if top_oos >= bot_oos:
        return 0.2
    return 0.8


def cpcv_gate(is_scores: list[float], oos_scores: list[float], max_pbo: float = 0.50) -> dict:
    pbo = probability_of_backtest_overfitting(is_scores, oos_scores)
    return {"pbo": pbo, "gate": "PASS" if pbo < max_pbo else "FAIL"}
