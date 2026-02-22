from omega_quant.data.reconciler import reconcile_prices
from omega_quant.data.sentiment_data import sentiment_overlay
from omega_quant.ops.ab_test import choose_variant, compare_variants
from omega_quant.research.recovery_factor import recovery_factor
from omega_quant.strategy.signals.correlation import correlation_guard


def test_reconcile_prices_pass_and_fail():
    ok = reconcile_prices([100, 101], [100.2, 100.9], tolerance_pct=0.5)
    assert ok["passed"]
    bad = reconcile_prices([100, 101], [102, 103], tolerance_pct=0.5)
    assert not bad["passed"]


def test_sentiment_overlay_bounds():
    assert 0.2 <= sentiment_overlay(0.6, 20) <= 1.1
    assert 0.2 <= sentiment_overlay(1.3, 70) <= 1.1


def test_correlation_guard():
    res = correlation_guard([1, 2, 3], [1, 2, 3], threshold=0.4)
    assert not res["passed"]
    assert res["action"] == "reduce_weight"


def test_ab_test_and_comparison():
    v = choose_variant("trade-123")
    assert v in {"A", "B"}
    cmp_res = compare_variants({"sharpe": 1.0, "max_dd": 0.2}, {"sharpe": 0.8, "max_dd": 0.4})
    assert cmp_res["winner"] == "A"


def test_recovery_factor():
    assert recovery_factor(30, 10) == 3.0
