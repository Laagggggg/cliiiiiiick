from pathlib import Path

from omega_quant.ui_service import run_action
from omega_quant.data.providers.csv_provider import CsvMarketDataProvider


def test_ui_actions_basic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [CsvMarketDataProvider()])

    run_action("reset_paper", {"starting_capital": 2500})
    paper = run_action("paper", {"starting_capital": 9999, "cycles": 1})
    assert paper["mode"] == "paper"
    assert paper["status"] in {"ok", "HALT"}

    account = run_action("paper_account")
    assert account["status"] == "ok"
    assert account["account"]["initial_equity"] == 2500

    proof = run_action("proof_check")
    assert proof["status"] in {"ok", "HALT"}

    audit = run_action("download_audit_pack")
    assert audit["status"] == "ok"
    assert Path("dist/paper_audit_pack.zip").exists()

    monitor = run_action("live_monitor")
    assert monitor["mode"] == "live_monitor"
    assert "shadow_decision" in monitor
    assert monitor["monitor_safe"] is True


def test_paper_run_blocked_when_proof_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    run_action("reset_paper", {"starting_capital": 2000})
    run_action("paper", {"starting_capital": 2000, "cycles": 1})
    p = Path("artifacts/paper_ledger.json")
    p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
    blocked = run_action("paper", {"starting_capital": 2000, "cycles": 1})
    assert blocked["status"] == "HALT"


def test_api_doctor_warn_without_keys(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    out = run_action("api_doctor")
    assert out["status"] == "WARN"


def test_websocket_fallback_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [CsvMarketDataProvider()])
    out = run_action("websocket_monitor")
    assert "POLLING" in out.get("transport", "")


def test_broker_paper_disabled_without_doctor(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    out = run_action("broker_paper_run", {"steps": 1})
    assert out["status"] == "HALT"
