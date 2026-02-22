from omega_quant.research.deflated_sharpe import deflated_sharpe_ratio
from omega_quant.research.gt_score import gt_score
from omega_quant.research.hansens_spa import hansens_spa
from omega_quant.research.monte_carlo import monte_carlo_sharpe
from omega_quant.research.whites_reality_check import whites_reality_check


def test_deflated_sharpe_ratio_shape():
    out = deflated_sharpe_ratio(observed_sharpe=1.2, sharpe_std=0.2, trials=50)
    assert 0.0 <= out["confidence"] <= 1.0
    assert out["gate"] in {"PASS", "FAIL"}


def test_gt_score_positive_case():
    s = gt_score(mean_return=0.01, z_stat=3.0, r2=0.4, downside_vol=0.02)
    assert s > 0


def test_whites_and_spa_proxies():
    # Scalar fallback path
    rc = whites_reality_check(best_strategy_return=0.12, bootstrap_mean_best=0.08)
    spa = hansens_spa(best_strategy_return=0.12, benchmark_return=0.05)
    assert rc["gate"] == "PASS"
    assert spa["gate"] == "PASS"


def test_whites_bootstrap_path():
    strat = [0.01, 0.005, 0.008, -0.002, 0.003, 0.006, 0.004, -0.001, 0.007, 0.002,
             0.005, 0.004, 0.003, 0.006, 0.001, 0.008, -0.003, 0.005, 0.004, 0.002]
    bench = [0.002, 0.001, 0.003, 0.001, -0.001, 0.002, 0.001, 0.0, 0.002, 0.001,
             0.001, 0.002, 0.001, 0.001, 0.0, 0.003, 0.001, 0.001, 0.002, 0.001]
    rc = whites_reality_check(strat, bench)
    assert "p_value" in rc
    assert "edge" in rc


def test_monte_carlo_sharpe():
    returns = [0.01, 0.005, -0.002, 0.004, 0.003, -0.001, 0.006]
    out = monte_carlo_sharpe(returns, paths=100, seed=7)
    assert "p5_sharpe" in out
    assert out["gate"] in {"PASS", "FAIL"}
