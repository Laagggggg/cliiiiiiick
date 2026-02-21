from __future__ import annotations

from omega_quant.types import GuardResult, State

REQUIRED_GUARDS = [
    "data_quality", "data_latency", "data_reconciliation", "macro_freshness", "corporate_action", "data_gap",
    "signal_confidence", "signal_nan", "mtf_alignment", "macro_floor",
    "daily_loss", "max_drawdown", "portfolio_heat", "dd_duration",
    "regime_allowed", "avoid_window", "hurst_random_walk",
    "broker_health", "state_persistence", "system_resources",
]


def default_checks() -> dict[str, bool]:
    return {g: False for g in REQUIRED_GUARDS}


def guard_all_v5(state: State) -> GuardResult:
    checks = {g: bool(state.checks.get(g, False)) for g in REQUIRED_GUARDS}

    # strict completeness: unknown/extra checks are ignored, missing required checks fail
    missing = [g for g in REQUIRED_GUARDS if g not in state.checks]
    if missing:
        return GuardResult(False, failed_guard=f"missing_checks:{','.join(missing)}", checks=checks)

    for g, passed in checks.items():
        if not passed:
            return GuardResult(False, failed_guard=g, checks=checks)

    if state.expectancy <= 0:
        return GuardResult(False, failed_guard="trade_expectancy", checks=checks)
    if state.consecutive_losses >= 5:
        return GuardResult(False, failed_guard="cooldown", checks=checks)
    if state.portfolio_heat > 0.06:
        return GuardResult(False, failed_guard="portfolio_heat_limit", checks=checks)
    return GuardResult(True, checks=checks)
