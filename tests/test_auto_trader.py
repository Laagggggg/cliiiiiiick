from omega_quant.ops.auto_trader import run_auto_trader
from omega_quant.ops.paper_cycle import run_paper_cycle
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import reset_account


def test_auto_trader_growth_fields():
    prices = [100, 101, 102, 103, 104, 103, 105, 106, 107]
    out = run_auto_trader(prices, starting_capital=1000)
    assert out["starting_capital"] == 1000
    assert "ending_capital" in out
    for t in out["trades"]:
        assert "equity_growth_dollars" in t
        assert "equity_growth_pct" in t


def test_paper_cycle_persists_compounding_and_proof(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(2000.0)

    out1 = run_paper_cycle(starting_capital=2000, cycles=1)
    eq1 = out1["result"]["ending_capital"]
    out2 = run_paper_cycle(starting_capital=9999, cycles=1)
    assert out2["result"]["starting_capital"] == eq1

    verify = verify_paper_result()
    assert verify["ok"] is True


def test_tamper_detected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reset_account(2000.0)
    run_paper_cycle(starting_capital=2000, cycles=1)

    p = tmp_path / "artifacts" / "paper_ledger.json"
    data = p.read_text(encoding="utf-8")
    p.write_text(data.replace("pnl_dollars", "pnl_dollars_tampered", 1), encoding="utf-8")

    verify = verify_paper_result()
    assert verify["ok"] is False
