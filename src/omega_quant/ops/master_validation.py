from __future__ import annotations

from omega_quant.live_gates import RISK_ACK_TEXT, live_gates
from omega_quant.ops.drift_detector import drift_gate
from omega_quant.ops.health import system_health
from omega_quant.research.report import go_no_go_checklist
from omega_quant.risk.guards import REQUIRED_GUARDS, guard_all_v5
from omega_quant.types import State


def master_validation(
    metrics: dict,
    expected_features: list[float],
    actual_features: list[float],
    *,
    confirm_live: bool = False,
    risk_ack: str = "",
    paper_days: int = 0,
    micro_live_days: int = 0,
    guard_checks: dict[str, bool] | None = None,
    consecutive_losses: int = 0,
    portfolio_heat: float = 0.01,
) -> dict:
    health = system_health()

    # Accept real guard state when provided; default to fail-closed (False)
    if guard_checks is not None:
        checks = {k: guard_checks.get(k, False) for k in REQUIRED_GUARDS}
    else:
        checks = {k: False for k in REQUIRED_GUARDS}
    checks["system_resources"] = health["passed"]
    guard = guard_all_v5(State(
        checks=checks,
        expectancy=metrics.get("expectancy", 0.0),
        consecutive_losses=consecutive_losses,
        portfolio_heat=portfolio_heat,
    ))

    research = go_no_go_checklist(metrics)
    drift = drift_gate(expected_features, actual_features)
    live = live_gates(confirm_live=confirm_live, risk_ack=risk_ack, paper_days=paper_days, micro_live_days=micro_live_days)

    release_ready = all([
        health["passed"],
        guard.passed,
        research["go"],
        drift["gate"] == "PASS",
    ])

    return {
        "health": health,
        "guard": {"passed": guard.passed, "failed_guard": guard.failed_guard},
        "research": research,
        "drift": drift,
        "live": live,
        "release_ready": release_ready,
        "risk_ack_template": RISK_ACK_TEXT,
    }
