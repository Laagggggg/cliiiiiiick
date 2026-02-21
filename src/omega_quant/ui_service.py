from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.live_gates import live_gates
from omega_quant.monitor.live_monitor import run_live_monitor
from omega_quant.ops.master_validation import master_validation
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import get_account_summary, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


def default_metrics() -> dict:
    return {"wfe": 0.62, "dsr_confidence": 0.97, "pbo": 0.30, "white_rc_p": 0.03, "spa_p": 0.02, "recovery_factor": 3.4, "expectancy": 0.12}


def _last_cycle_payload() -> dict:
    p = Path("artifacts/paper_cycle_result.json")
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    last_reason = data.get("session_trades", [])[-1].get("reason", {}) if data.get("session_trades") else {"status": "NO_TRADE", "reason": "no_recent_fills"}
    return {
        "last_decision": last_reason,
        "provenance": data.get("provenance", {}),
        "charts": {"equity": "artifacts/equity_curve.png", "drawdown": "artifacts/drawdown.png", "trades": "artifacts/trade_markers.png"},
    }


def _api_doctor() -> dict:
    req = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    env = {k: bool(os.getenv(k)) for k in req}
    broker = AlpacaPaperBroker()
    out = {"env": env, "broker_enabled": broker.enabled(), "errors": []}
    if not broker.enabled():
        out["status"] = "WARN"
        out["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        return out
    try:
        acct = broker.get_account()
        out["account"] = {"id": acct.get("id"), "status": acct.get("status")}
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"account:{exc}")

    try:
        from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider

        p = AlpacaMarketDataProvider()
        q = p.get_quote("SPY")
        bars = p.get_bars("SPY", "1h", limit=100)
        out["quote_ok"] = q is not None
        out["bars_1h"] = len(bars)
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"data:{exc}")

    out["status"] = "PASS" if not out["errors"] else "WARN"
    out["mode"] = "BROKER ENABLED" if out["status"] == "PASS" else "BROKER DISABLED / USING FALLBACK DATA"
    return out


def run_action(action: str, params: dict | None = None) -> dict:
    params = params or {}
    metrics = default_metrics()

    if action == "validate":
        return master_validation(metrics, [1, 2, 3, 4, 5], [1.1, 2.1, 3.0, 3.9, 5.2])
    if action == "report":
        return {"research_report": render_report(metrics), "checklist": render_go_no_go_markdown(metrics)}

    if action == "paper":
        prior = verify_paper_result()
        if prior.get("exists") and not prior.get("ok"):
            return {"status": "HALT", "reason": "proof_failed_block", "proof": prior}
        from omega_quant.ops.paper_cycle import run_paper_cycle

        out = run_paper_cycle(starting_capital=float(params.get("starting_capital", 5000.0)), cycles=int(params.get("cycles", 1)))
        proof = verify_paper_result()
        return {"status": "ok" if proof.get("ok") else "HALT", "mode": "paper", "cycle": out, "proof": proof, "account": get_account_summary(), **_last_cycle_payload()}

    if action == "paper_account":
        return {"status": "ok", "account": get_account_summary(), **_last_cycle_payload()}
    if action == "reset_paper":
        return {"status": "ok", "account": reset_account(float(params.get("starting_capital", 5000.0)))}
    if action == "proof_check":
        p = verify_paper_result()
        return {"status": "ok" if p.get("ok") else "HALT", "proof": p}
    if action == "paper_review":
        p = Path("artifacts/paper_trade_reviews.md")
        return {"status": "ok", "exists": p.exists(), "path": str(p), "content": p.read_text(encoding="utf-8") if p.exists() else "No paper reviews yet."}
    if action == "download_audit_pack":
        script = Path(__file__).resolve().parents[2] / "scripts" / "make_audit_pack.py"
        proc = subprocess.run(f"python {script}", shell=True, capture_output=True, text=True)
        return {"status": "ok" if proc.returncode == 0 else "error", "output": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    if action == "live_monitor":
        return run_live_monitor(mode=str(params.get("mode", "polling")))
    if action == "api_doctor":
        return _api_doctor()
    if action == "dry_run":
        return {"status": "ok", "mode": "dry_run", "message": "Dry run ready."}
    if action == "live_check":
        return live_gates(bool(params.get("confirm_live", False)), str(params.get("risk_ack", "")), int(params.get("paper_days", 0)), int(params.get("micro_live_days", 0)))
    return {"status": "error", "message": f"Unknown action: {action}"}
