from omega_quant.ops.drift_detector import drift_gate, population_stability_index
from omega_quant.research.cpcv import cpcv_gate, probability_of_backtest_overfitting
from omega_quant.research.factor_decomposition import factor_decomposition


def test_cpcv_not_implemented_label():
    assert probability_of_backtest_overfitting([1.0, 0.8, 0.4], [0.9, 0.5, 0.2]) is None
    out = cpcv_gate([1, 0.8, 0.4], [0.9, 0.5, 0.2])
    assert out["gate"] == "NOT_IMPLEMENTED"
    assert "NOT IMPLEMENTED" in out["label"]


def test_factor_decomposition_keys():
    out = factor_decomposition([0.02, 0.01, -0.01, 0.03], [0.01, 0.0, -0.02, 0.02])
    assert set(out.keys()) == {"alpha", "beta", "r2"}
    assert 0.0 <= out["r2"] <= 1.0


def test_drift_detector():
    psi_same = population_stability_index([1, 2, 3, 4], [1, 2, 3, 4])
    psi_shifted = population_stability_index([1, 2, 3, 4], [10, 11, 12, 13])
    assert psi_same <= psi_shifted
    assert drift_gate([1, 2, 3, 4], [1, 2, 3, 4])["gate"] == "PASS"
