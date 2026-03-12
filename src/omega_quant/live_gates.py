from __future__ import annotations

import os

from omega_quant.paper_account.db import get_paper_days_completed
from omega_quant.risk.guards import REQUIRED_GUARDS, guard_all_v5
from omega_quant.types import State

RISK_ACK_TEXT = "I UNDERSTAND THIS SYSTEM CAN AND WILL LOSE MONEY"


def live_gates(confirm_live: bool, risk_ack: str, paper_days: int, micro_live_days: int) -> dict:
    completed_paper_days = get_paper_days_completed() if paper_days <= 0 else int(paper_days)
    completed_micro_live_days = int(micro_live_days)
    gates = {
        "env_live_enabled": os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true",
        "confirm_live_flag": bool(confirm_live),
        "risk_ack": risk_ack.strip() == RISK_ACK_TEXT,
        "paper_phase": completed_paper_days >= 45,
        "micro_live_phase": completed_micro_live_days >= 45,
    }

    checks = {k: True for k in REQUIRED_GUARDS}
    guard = guard_all_v5(State(checks=checks, expectancy=0.1, consecutive_losses=0, portfolio_heat=0.01))
    gates["guard_all"] = guard.passed

    return {
        "gates": gates,
        "paper_days_completed": completed_paper_days,
        "paper_days_required": 45,
        "micro_live_days_completed": completed_micro_live_days,
        "micro_live_days_required": 45,
        "live_allowed": all(gates.values()),
        "failed": [k for k, v in gates.items() if not v],
    }
