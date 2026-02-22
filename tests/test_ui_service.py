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
    assert "decision_sentence" in paper

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


def test_paper_run_blocked_when_proof_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("omega_quant.ops.paper_cycle.get_provider_chain", lambda: [CsvMarketDataProvider()])
    run_action("reset_paper", {"starting_capital": 2000})
    run_action("paper", {"starting_capital": 2000, "cycles": 1})
    p = Path("artifacts/paper_ledger.json")
    p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
    blocked = run_action("paper", {"starting_capital": 2000, "cycles": 1})
    assert blocked["status"] == "HALT"


def test_api_doctor_required_fields(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    out = run_action("api_doctor")
    for key in ["ws_available", "ws_health", "provider_primary", "provider_secondary", "broker_enabled", "last_bar_ts", "freshness_seconds", "next_action"]:
        assert key in out


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


def test_ui_truth_payload_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_action("reset_paper", {"starting_capital": 2000})
    out = run_action("paper_account")
    assert "mode_truth" in out
    assert "transport" in out
    assert "freshness_seconds" in out
    assert "last_bar_ts" in out
    assert "provider_primary" in out
    assert "provider_secondary" in out
    assert "reconciliation" in out


def test_replay_live_stream_action(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from omega_quant.monitor.live_ws import _ingest_raw

    _ingest_raw({"T": "q", "S": "SPY", "bp": 99.0, "ap": 99.1, "t": "2026-01-01T02:00:00Z"})
    out = run_action("replay_live_stream")
    assert out["status"] == "ok"
