from omega_quant.ui_service import run_action


def test_csv_sample_mode_truth_and_freshness_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_action("reset_paper", {"starting_capital": 1000})
    out = run_action("paper_account")
    assert out["mode_truth"] == "DEMO"
    assert out["data_grade"] == "CSV_SAMPLE"
    assert out["freshness_label"] == "N/A (static sample)"
    assert "Set ALPACA_API_KEY" in out["next_action"]


def test_truth_fields_non_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action("reset_paper", {"starting_capital": 1000})
    for k in ["mode_truth", "transport", "provider_primary", "freshness_label", "last_bar_ts", "next_action", "data_grade"]:
        assert k in out
        assert str(out[k]).strip() != ""
