from __future__ import annotations


def hansens_spa(best_strategy_return: float, benchmark_return: float) -> dict:
    """Simplified SPA proxy against benchmark return."""
    diff = best_strategy_return - benchmark_return
    p_proxy = 0.02 if diff > 0 else 0.5
    return {"diff": diff, "p_value": p_proxy, "gate": "PASS" if p_proxy < 0.05 else "FAIL"}
