from omega_quant.ops.auto_trader import run_auto_trader
from omega_quant.ops.paper_cycle import run_paper_cycle


def test_auto_trader_growth_fields():
    prices = [100, 101, 102, 103, 104, 103, 105, 106, 107]
    out = run_auto_trader(prices, starting_capital=1000)
    assert out["starting_capital"] == 1000
    assert "ending_capital" in out
    assert "trades" in out
    for t in out["trades"]:
        assert "equity_growth_dollars" in t
        assert "equity_growth_pct" in t


def test_paper_cycle_writes_proof(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_paper_cycle(starting_capital=2000, cycles=1)
    assert out["proof_file"].endswith("paper_proof_report.md")
    assert (tmp_path / "artifacts" / "paper_proof_report.md").exists()
    assert (tmp_path / "artifacts" / "paper_cycle_result.json").exists()
