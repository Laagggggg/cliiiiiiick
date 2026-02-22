from __future__ import annotations


def round_trip_cost_bps(spread_bps: float, slippage_bps: float, impact_bps: float, commission_bps: float = 0.0) -> float:
    """Total round-trip cost in bps: 2 * (entry+exit components)."""
    one_way = max(0.0, spread_bps) + max(0.0, slippage_bps) + max(0.0, impact_bps) + max(0.0, commission_bps)
    return 2.0 * one_way


def stress_cost_bps(base_cost_bps: float, stress_multiple: float = 6.0) -> float:
    return max(0.0, base_cost_bps) * max(1.0, stress_multiple)
