from omega_quant.ui_service import run_action


REQUIRED = [
    "mode_truth",
    "data_grade",
    "transport",
    "provider_primary",
    "provider_secondary",
    "recon_status",
    "freshness_seconds",
    "freshness_label",
    "last_bar_ts",
    "next_action",
    "decision_sentence",
    "freshness_basis",
    "live_verified",
]


def test_csv_sample_mode_truth_and_freshness_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_action("reset_paper", {"starting_capital": 1000})
    out = run_action("paper_account")
    assert out["mode_truth"] == "DEMO"
    assert out["data_grade"] == "CSV_SAMPLE"
    assert out["freshness_label"] == "N/A (static sample)"
    assert "ALPACA_API_KEY" in out["next_action"]


def test_truth_fields_non_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action("reset_paper", {"starting_capital": 1000})
    for k in REQUIRED:
        assert k in out
        assert str(out[k]).strip() != ""


def test_fill_model_present_and_confidence_labels(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_action("reset_paper", {"starting_capital": 1000})
    out = run_action("paper_account")
    assert out["fill_model"] == "SIM_OHLC_LIMIT"
    assert "(n=" in out["account"]["win_rate_label"]


def test_decision_sentence_has_status_and_next(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action("reset_paper", {"starting_capital": 1000})
    assert "Next:" in out["decision_sentence"]
    assert any(out["decision_sentence"].startswith(x) for x in ["HALT:", "NO_TRADE:", "TRADE:", "WARN:", "OK:", "ok:"])
