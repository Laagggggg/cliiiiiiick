from omega_quant.ui_service import run_action


def test_ui_actions_basic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert "health" in run_action("validate")
    rep = run_action("report")
    assert "research_report" in rep and "checklist" in rep

    run_action("reset_paper", {"starting_capital": 2500})
    paper = run_action("paper", {"starting_capital": 9999, "cycles": 1})
    assert paper["mode"] == "paper"
    assert "cycle" in paper

    account = run_action("paper_account")
    assert account["status"] == "ok"
    assert account["account"]["equity"] > 0

    review = run_action("paper_review")
    assert review["status"] == "ok"
    assert "content" in review

    proof = run_action("proof_check")
    assert proof["status"] in {"ok", "HALT"}

    audit = run_action("download_audit_pack")
    assert audit["status"] == "ok"

    monitor = run_action("live_monitor")
    assert monitor["mode"] == "live_monitor"

    assert run_action("dry_run")["mode"] == "dry_run"


def test_ui_live_check():
    out = run_action(
        "live_check",
        {
            "confirm_live": True,
            "risk_ack": "I UNDERSTAND THIS SYSTEM CAN AND WILL LOSE MONEY",
            "paper_days": 45,
            "micro_live_days": 45,
        },
    )
    assert "live_allowed" in out
