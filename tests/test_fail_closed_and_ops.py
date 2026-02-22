from omega_quant.ops.health import system_health
from omega_quant.risk.guards import REQUIRED_GUARDS, default_checks, guard_all_v5
from omega_quant.strategy.regime_state_machine import RegimeStateMachine
from omega_quant.types import Regime, State


def test_default_checks_all_false():
    checks = default_checks()
    assert set(checks.keys()) == set(REQUIRED_GUARDS)
    assert all(v is False for v in checks.values())


def test_guard_fails_when_missing_required_check():
    checks = {k: True for k in REQUIRED_GUARDS}
    checks.pop("data_quality")
    result = guard_all_v5(State(checks=checks, expectancy=1.0, consecutive_losses=0, portfolio_heat=0.01))
    assert not result.passed
    assert result.failed_guard.startswith("missing_checks:")


def test_guard_fails_on_heat_limit():
    checks = {k: True for k in REQUIRED_GUARDS}
    result = guard_all_v5(State(checks=checks, expectancy=1.0, consecutive_losses=0, portfolio_heat=0.2))
    assert not result.passed
    assert result.failed_guard == "portfolio_heat_limit"


def test_regime_state_machine_transitions():
    sm = RegimeStateMachine()
    assert sm.step(Regime.TRENDING) == Regime.RANGING
    assert sm.step(Regime.TRENDING) == Regime.RANGING
    assert sm.step(Regime.TRENDING) == Regime.TRENDING
    assert sm.step(Regime.AVOID) == Regime.AVOID


def test_health_schema():
    health = system_health()
    assert "passed" in health
    assert "checks" in health
    assert "disk_ok" in health["checks"]
    assert "load_ok" in health["checks"]
