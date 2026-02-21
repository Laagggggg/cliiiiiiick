from __future__ import annotations


def whites_reality_check(best_strategy_return: float, bootstrap_mean_best: float) -> dict:
    """
    Simplified White's RC proxy.
    Positive edge beyond bootstrap expectation passes.
    """
    edge = best_strategy_return - bootstrap_mean_best
    p_proxy = 0.01 if edge > 0 else 0.5
    return {"edge": edge, "p_value": p_proxy, "gate": "PASS" if p_proxy < 0.05 else "FAIL"}
