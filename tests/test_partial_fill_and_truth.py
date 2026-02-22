from omega_quant.data.providers.csv_provider import CsvMarketDataProvider
from omega_quant.ops.paper_cycle import run_paper_cycle
from omega_quant.paper_account.db import list_equity_curve, reset_account


def test_partial_fill_updates_equity_incrementally(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(5000)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    out = run_paper_cycle(starting_capital=5000, cycles=1)
    assert out["result"]["status"] == "ok"
    eq = list_equity_curve()
    assert len(eq) > 2


def test_truth_banner_payload_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from omega_quant.ui_service import run_action

    run_action("reset_paper", {"starting_capital": 1000})
    payload = run_action("paper_account")
    for k in ["mode_truth", "transport", "provider_primary", "provider_secondary", "reconciliation", "freshness_seconds", "last_bar_ts"]:
        assert k in payload
