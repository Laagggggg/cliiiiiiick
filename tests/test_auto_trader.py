import hashlib
from pathlib import Path

from omega_quant.ops.paper_cycle import _fill_entry, run_paper_cycle
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import reset_account
from omega_quant.data.providers.csv_provider import CsvMarketDataProvider


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_limit_fill_inside_ohlc_only():
    bar = {"open": 100, "high": 102, "low": 99, "close": 101}
    assert _fill_entry(101, bar, market_order=False, slip=0) == 101
    assert _fill_entry(103, bar, market_order=False, slip=0) is None


def test_compounding_persists_across_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    reset_account(2000.0)
    out1 = run_paper_cycle(starting_capital=2000, cycles=1)
    start2 = out1["result"]["ending_capital"]
    out2 = run_paper_cycle(starting_capital=9999, cycles=1)
    assert out2["result"]["starting_capital"] == start2


def test_determinism_same_dataset_same_checksums(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    reset_account(2000.0)
    run_paper_cycle(starting_capital=2000, cycles=1)
    h1 = _sha(Path("artifacts/checksums.sha256"))
    reset_account(2000.0)
    run_paper_cycle(starting_capital=2000, cycles=1)
    h2 = _sha(Path("artifacts/checksums.sha256"))
    assert h1 == h2


def test_tamper_detected_and_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    reset_account(2000.0)
    run_paper_cycle(starting_capital=2000, cycles=1)
    p = Path("artifacts/paper_ledger.json")
    p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
    verify = verify_paper_result()
    assert verify["ok"] is False


def test_charts_exist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    reset_account(2000.0)
    run_paper_cycle(starting_capital=2000, cycles=1)
    assert Path("artifacts/equity_curve.png").exists()
    assert Path("artifacts/drawdown.png").exists()
