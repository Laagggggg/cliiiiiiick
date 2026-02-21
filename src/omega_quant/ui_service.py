from __future__ import annotations

from pathlib import Path
import subprocess

from omega_quant.data.providers import get_provider_chain
from omega_quant.engine import run_step
from omega_quant.live_gates import live_gates
from omega_quant.ops.master_validation import master_validation
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import get_account_summary, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


RISK_ACK_TEXT = "I UNDERSTAND THIS SYSTEM CAN AND WILL LOSE MONEY"


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


def _live_monitor() -> dict:
    errors: list[str] = []
    for provider in get_provider_chain():
        try:
            bars = provider.get_bars("SPY", "1d", limit=40)
            latest = bars[-1]
            closes = [b.close for b in bars]
            shadow = run_step(closes=closes, equity=5000.0)
            return {
                "status": "ok",
                "mode": "live_monitor",
                "source": provider.source_name(),
                "latest_bar": {
                    "timestamp": latest.timestamp,
                    "close": latest.close,
                    "volume": latest.volume,
                },
                "readiness": "GREEN" if len(bars) >= 20 else "YELLOW",
                "shadow_decision": {
                    "status": shadow["status"],
                    "reason": shadow.get("reason", ""),
                    "score": shadow.get("score", 0.0),
                    "threshold": shadow.get("threshold", 0.0),
                    "regime": shadow.get("regime", "UNKNOWN"),
                },
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{provider.source_name()}:{exc}")
    return {"status": "HALT", "mode": "live_monitor", "errors": errors, "readiness": "RED"}


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
        return {"status": "ok", "mode": "paper", "cycle": out, "account": get_account_summary()}

    if action == "paper_account":
        return {"status": "ok", "account": get_account_summary()}

    if action == "reset_paper":
        starting_capital = float(params.get("starting_capital", 5000.0))
        return {"status": "ok", "account": reset_account(starting_capital)}

    if action == "proof_check":
        proof = verify_paper_result()
        return {"status": "ok" if proof.get("ok") else "HALT", "proof": proof}

    if action == "paper_review":
        p = Path("artifacts/paper_trade_reviews.md")
        return {
            "status": "ok",
            "exists": p.exists(),
            "path": str(p),
            "content": p.read_text(encoding="utf-8") if p.exists() else "No paper reviews yet. Run Paper Trading Mode first.",
        }

    if action == "download_audit_pack":
        script = Path(__file__).resolve().parents[2] / "scripts" / "make_audit_pack.py"
        proc = subprocess.run(f"python {script}", shell=True, capture_output=True, text=True)
        return {"status": "ok" if proc.returncode == 0 else "error", "output": proc.stdout.strip(), "stderr": proc.stderr.strip()}

    if action == "live_monitor":
        return _live_monitor()

    if action == "dry_run":
        return {
            "status": "ok",
            "mode": "dry_run",
            "message": "Dry run ready. Use main_dry_run.py for execution simulation.",
        }

    if action == "live_check":
        confirm_live = bool(params.get("confirm_live", False))
        risk_ack = str(params.get("risk_ack", ""))
        paper_days = int(params.get("paper_days", 0))
        micro_live_days = int(params.get("micro_live_days", 0))
        return live_gates(confirm_live, risk_ack, paper_days, micro_live_days)

    return {"status": "error", "message": f"Unknown action: {action}"}
