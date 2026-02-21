from omega_quant.ops.paper_cycle import run_paper_cycle
from omega_quant.paper_account.db import reset_account


def test_reconciliation_halt(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    reset_account(1000)

    monkeypatch.setattr("omega_quant.ops.paper_cycle.reconcile_prices", lambda *a, **k: {"passed": False, "max_diff_pct": 99})
    out = run_paper_cycle(starting_capital=1000, cycles=1)
    assert out["status"] == "HALT"
    assert out["reason"] == "reconciliation_failed"
