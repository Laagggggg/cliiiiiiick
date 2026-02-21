from omega_quant.risk.circuit_breaker import circuit_breaker_level
from omega_quant.risk.dd_duration import drawdown_duration, duration_escalation
from omega_quant.risk.sizing import calculate_position_size_v5, hurst_multiplier


def test_drawdown_duration():
    eq = [100, 105, 103, 101, 102, 99]
    assert drawdown_duration(eq) == 4


def test_duration_escalation():
    assert duration_escalation(10) == "NORMAL"
    assert duration_escalation(31) == "ESCALATE_ONE_LEVEL"
    assert duration_escalation(61) == "FORCE_ORANGE"


def test_circuit_breaker_with_duration_escalation():
    assert circuit_breaker_level(0.02, 0) == "GREEN"
    assert circuit_breaker_level(0.02, 31) == "YELLOW"
    assert circuit_breaker_level(0.02, 61) == "ORANGE"
    assert circuit_breaker_level(0.16, 0) == "RED"


def test_hurst_multiplier_bounds():
    assert 0.70 <= hurst_multiplier(0.5) <= 1.15
    assert 0.70 <= hurst_multiplier(0.9) <= 1.15


def test_position_sizing_respects_heat_and_min_ticket():
    size = calculate_position_size_v5(
        capital=2000,
        entry=100,
        atr=2,
        signal_conf=0.8,
        regime_conf=0.8,
        alignment=0.9,
        macro=1.0,
        hurst=0.65,
        cb_mult=1.0,
        portfolio_heat_remaining=20,
    )
    assert size >= 0
    # $20 heat with 2*ATR=4 implies max 5 shares
    assert size <= 5
