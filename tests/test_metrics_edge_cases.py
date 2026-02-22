from omega_quant.paper_account.db import get_account_summary, open_position, reset_account


def test_profit_factor_no_losses_is_inf_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(1000)
    open_position("2026-01-01T00:00:00Z", "SPY", 1.0, 100.0, 0.0)
    out = get_account_summary()
    assert out["profit_factor"] is None
    assert out["profit_factor_label"] in {"INF", "N/A"}


def test_expectancy_low_sample_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(1000)
    out = get_account_summary()
    assert out["expectancy_confidence"] == "low sample"
    assert "(n=" in out["win_rate_label"]
