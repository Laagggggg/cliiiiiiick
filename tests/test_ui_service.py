from pathlib import Path

from omega_quant.ui_service import run_action


def test_ui_actions_basic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_action("reset_paper", {"starting_capital": 2500})

    paper = run_action("paper", {"starting_capital": 9999, "cycles": 1})
    assert paper["mode"] == "paper"
    assert paper["status"] in {"ok", "HALT"}
    assert "account" in paper

    account = run_action("paper_account")
    assert account["status"] == "ok"
    assert "provenance" in account

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
    run_action("reset_paper", {"starting_capital": 2000})
    run_action("paper", {"starting_capital": 2000, "cycles": 1})
    p = Path("artifacts/paper_ledger.json")
    p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
    blocked = run_action("paper", {"starting_capital": 2000, "cycles": 1})
    assert blocked["status"] == "HALT"
    assert blocked["reason"] == "proof_failed_block"
