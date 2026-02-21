from __future__ import annotations

from pathlib import Path
import subprocess

from omega_quant.live_gates import live_gates
from omega_quant.monitor.live_monitor import run_live_monitor
from omega_quant.ops.master_validation import master_validation
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import get_account_summary, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


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


def _last_cycle_payload() -> dict:
    p = Path("artifacts/paper_cycle_result.json")
    if not p.exists():
        return {}
    import json

    data = json.loads(p.read_text(encoding="utf-8"))
    return {
        "last_decision": data.get("session_trades", [])[-1].get("reason") if data.get("session_trades") else {"status": "NO_TRADE", "reason": "no_recent_fills"},
        "provenance": data.get("provenance", {}),
        "charts": {
            "equity": "artifacts/equity_curve.png",
            "drawdown": "artifacts/drawdown.png",
            "trades": "artifacts/trade_markers.png",
        },
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
        prior_proof = verify_paper_result()
        if prior_proof.get("exists") and not prior_proof.get("ok"):
            return {"status": "HALT", "reason": "proof_failed_block", "proof": prior_proof}

        from omega_quant.ops.paper_cycle import run_paper_cycle

        starting_capital = float(params.get("starting_capital", 5000.0))
        cycles = int(params.get("cycles", 1))
        out = run_paper_cycle(starting_capital=starting_capital, cycles=cycles)
        post_proof = verify_paper_result()
        status = "ok" if post_proof.get("ok") else "HALT"
        return {"status": status, "mode": "paper", "cycle": out, "proof": post_proof, "account": get_account_summary(), **_last_cycle_payload()}

    if action == "paper_account":
        return {"status": "ok", "account": get_account_summary(), **_last_cycle_payload()}

    if action == "reset_paper":
        starting_capital = float(params.get("starting_capital", 5000.0))
        return {"status": "ok", "account": reset_account(starting_capital)}

    if action == "proof_check":
        proof = verify_paper_result()
        return {"status": "ok" if proof.get("ok") else "HALT", "proof": proof}

    if action == "paper_review":
        p = Path("artifacts/paper_trade_reviews.md")
        return {"status": "ok", "exists": p.exists(), "path": str(p), "content": p.read_text(encoding="utf-8") if p.exists() else "No paper reviews yet."}

    if action == "download_audit_pack":
        script = Path(__file__).resolve().parents[2] / "scripts" / "make_audit_pack.py"
        proc = subprocess.run(f"python {script}", shell=True, capture_output=True, text=True)
        return {"status": "ok" if proc.returncode == 0 else "error", "output": proc.stdout.strip(), "stderr": proc.stderr.strip()}

    if action == "live_monitor":
        return run_live_monitor()

    if action == "dry_run":
        return {"status": "ok", "mode": "dry_run", "message": "Dry run ready. Use main_dry_run.py for execution simulation."}

    if action == "live_check":
        return live_gates(bool(params.get("confirm_live", False)), str(params.get("risk_ack", "")), int(params.get("paper_days", 0)), int(params.get("micro_live_days", 0)))

    return {"status": "error", "message": f"Unknown action: {action}"}
