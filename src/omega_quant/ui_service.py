from __future__ import annotations

from omega_quant.live_gates import live_gates
from omega_quant.ops.master_validation import master_validation
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report
from omega_quant.ops.proof_check import verify_paper_result
from pathlib import Path



def default_metrics() -> dict:
    return {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }


def run_action(action: str, params: dict | None = None) -> dict:
    params = params or {}
    metrics = default_metrics()

    if action == "validate":
        return master_validation(metrics, [1, 2, 3, 4, 5], [1.1, 2.1, 3.0, 3.9, 5.2])

    if action == "report":
        return {
            "research_report": render_report(metrics),
            "checklist": render_go_no_go_markdown(metrics),
        }

    if action == "paper":
        from omega_quant.ops.paper_cycle import run_paper_cycle

        starting_capital = float(params.get("starting_capital", 5000.0))
        cycles = int(params.get("cycles", 1))
        out = run_paper_cycle(starting_capital=starting_capital, cycles=cycles)
        return {"status": "ok", "mode": "paper", "cycle": out}

    if action == "dry_run":
        return {
            "status": "ok",
            "mode": "dry_run",
            "message": "Dry run ready. Use main_dry_run.py for execution simulation.",
        }


    if action == "paper_review":
        p = Path("artifacts/paper_trade_reviews.md")
        return {"status": "ok", "exists": p.exists(), "path": str(p), "content": p.read_text(encoding="utf-8") if p.exists() else "No paper reviews yet. Run Paper Trading Mode first."}


    if action == "proof_check":
        return verify_paper_result()

    if action == "live_check":
        confirm_live = bool(params.get("confirm_live", False))
        risk_ack = str(params.get("risk_ack", ""))
        paper_days = int(params.get("paper_days", 0))
        micro_live_days = int(params.get("micro_live_days", 0))
        return live_gates(confirm_live, risk_ack, paper_days, micro_live_days)

    return {"status": "error", "message": f"Unknown action: {action}"}
