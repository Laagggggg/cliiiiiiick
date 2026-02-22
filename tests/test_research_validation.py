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
    rc = whites_reality_check(0.12, 0.08)
    spa = hansens_spa(0.12, 0.05)
    assert rc["gate"] == "PASS"
    assert spa["gate"] == "PASS"


def test_monte_carlo_sharpe():
    returns = [0.01, 0.005, -0.002, 0.004, 0.003, -0.001, 0.006]
    out = monte_carlo_sharpe(returns, paths=100, seed=7)
    assert "p5_sharpe" in out
    assert out["gate"] in {"PASS", "FAIL"}
