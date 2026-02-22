from datetime import datetime

from omega_quant.execution.gap_risk_handler import assess_gap_risk
from omega_quant.execution.partial_fill_handler import handle_partial_fill
from omega_quant.risk.equity_curve_gate import equity_curve_gate
from omega_quant.risk.guards import REQUIRED_GUARDS, guard_all_v5
from omega_quant.risk.mae_mfe import MAEOptimizedStops
from omega_quant.risk.portfolio_heat import calculate_portfolio_heat
from omega_quant.risk.trade_expectancy import compute_trade_expectancy
from omega_quant.types import Position, State, Trade


def test_portfolio_heat():
    heat = calculate_portfolio_heat([Position("SPY", 10, 100, 98)], capital=2000)
    assert heat == 0.01


def test_expectancy_positive_gate():
    trades = [Trade(10), Trade(-5), Trade(8), Trade(-4), Trade(6)]
    result = compute_trade_expectancy(trades)
    assert result["gate"] == "PASS"


def test_mae_fallback_when_not_enough_samples():
    m = MAEOptimizedStops(min_sample=5)
    assert m.compute_optimal_stop([Trade(1, 1.0, 2.0)]) == 2.0


def test_guard_all_v5():
    state = State(checks={k: True for k in REQUIRED_GUARDS}, expectancy=1.0, consecutive_losses=0)
    assert guard_all_v5(state).passed


def test_partial_fill_handler_requeue():
    action, qty = handle_partial_fill(10, 100, signal_strength=0.8, entry_threshold=0.5, min_partial_fill_pct=0.5)
    assert action == "REQUEUE"
    assert qty == 90


def test_gap_risk_high():
    level, score = assess_gap_risk("15:55", vix=30, earnings_tomorrow=True, now=datetime(2026, 1, 2))
    assert level == "HIGH"
    assert score >= 6


def test_equity_curve_gate_halt():
    eq = [100.0] * 60 + [70.0]
    assert equity_curve_gate(eq, lookback=50) in {"HALT", "REDUCE_50"}
