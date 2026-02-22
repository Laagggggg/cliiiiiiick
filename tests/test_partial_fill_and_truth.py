from omega_quant.data.providers.csv_provider import CsvMarketDataProvider
from omega_quant.ops.paper_cycle import run_paper_cycle
from omega_quant.paper_account.db import _connect, get_open_position, list_equity_curve, open_position, reset_account


def test_partial_fill_updates_equity_incrementally(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(5000)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    out = run_paper_cycle(starting_capital=5000, cycles=1)
    assert out["result"]["status"] == "ok"
    eq = list_equity_curve()
    assert len(eq) > 2


def test_partial_fill_weighted_avg_and_qty_invariants(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(1000)
    open_position("2026-01-01T00:00:00Z", "SPY", 1.0, 100.0, 0.0)
    open_position("2026-01-01T00:01:00Z", "SPY", 2.0, 110.0, 0.0)
    pos = get_open_position("SPY")
    assert round(pos["qty"], 6) == 3.0
    assert round(pos["avg_entry"], 6) == round((1.0 * 100.0 + 2.0 * 110.0) / 3.0, 6)


def test_truth_banner_payload_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from omega_quant.ui_service import run_action

    run_action("reset_paper", {"starting_capital": 1000})
    payload = run_action("paper_account")
    for k in ["mode_truth", "transport", "provider_primary", "provider_secondary", "reconciliation", "freshness_seconds", "last_bar_ts"]:
        assert k in payload


def test_equity_curve_updates_after_fill_slices(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(1000)
    open_position("2026-01-01T00:00:00Z", "SPY", 0.5, 100.0, 0.0)
    open_position("2026-01-01T00:01:00Z", "SPY", 0.5, 100.0, 0.0)
    with _connect("artifacts/paper_account.sqlite") as conn:
        c = conn.execute("SELECT COUNT(*) FROM equity_curve").fetchone()[0]
    assert c >= 3
