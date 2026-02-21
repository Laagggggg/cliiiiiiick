from omega_quant.ui_service import run_action


def test_ui_actions_basic():
    assert "health" in run_action("validate")
    rep = run_action("report")
    assert "research_report" in rep and "checklist" in rep

    paper = run_action("paper", {"starting_capital": 2500, "cycles": 1})
    assert paper["mode"] == "paper"
    assert "cycle" in paper

    review = run_action("paper_review")
    assert review["status"] == "ok"
    assert "content" in review

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
