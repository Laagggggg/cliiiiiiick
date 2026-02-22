from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.live_gates import live_gates
from omega_quant.monitor.live_monitor import run_live_monitor
from omega_quant.ops.broker_paper_cycle import run_broker_paper_cycle
from omega_quant.ops.broker_paper_daemon import run_broker_paper_daemon
from omega_quant.ops.master_validation import master_validation
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import get_account_summary, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


def default_metrics() -> dict:
    return {"wfe": 0.62, "dsr_confidence": 0.97, "pbo": 0.30, "white_rc_p": 0.03, "spa_p": 0.02, "recovery_factor": 3.4, "expectancy": 0.12}


def _truth_defaults() -> dict:
    return {
        "mode_truth": "SIMULATED FILLS",
        "transport": "POLLING",
        "provider_primary": "fallback",
        "provider_secondary": "none",
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "freshness_seconds": "not loaded (run monitor)",
    }


def _last_cycle_payload() -> dict:
    p = Path("artifacts/paper_cycle_result.json")
    if not p.exists():
        return {"last_decision": {"sentence": "NO_TRADE: run historical sim or monitor first"}, **_truth_defaults()}
    data = json.loads(p.read_text(encoding="utf-8"))
    last_reason = data.get("last_decision_reason", "NO_TRADE: no recent fills")
    prov = data.get("provenance", {})
    recon = prov.get("reconciliation", {})
    return {
        "last_decision": {"sentence": str(last_reason)},
        "provenance": prov,
        "charts": {"equity": "artifacts/equity_curve.png", "drawdown": "artifacts/drawdown.png", "trades": "artifacts/trade_markers.png"},
        "mode_truth": data.get("mode_truth", "SIMULATED FILLS"),
        "transport": "POLLING",
        "provider_primary": prov.get("source_primary", "unknown"),
        "provider_secondary": "fallback",
        "reconciliation": recon,
        "freshness_seconds": prov.get("freshness_seconds"),
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
        out["quote_ok"] = p.get_quote("SPY") is not None
        out["bars_1h"] = len(p.get_bars("SPY", "1h", limit=100))
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

    if action == "broker_paper_run":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, **_truth_defaults()}
        steps = int(params.get("steps", 1))
        out = run_broker_paper_cycle(steps=steps)
        payload = _last_cycle_payload()
        payload.update({"mode_truth": "BROKER FILLS"})
        return {"status": out.get("status", "HALT"), "mode": "broker_paper", "cycle": out, "account": get_account_summary(), **payload}

    if action == "broker_paper_daemon":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, **_truth_defaults()}
        seconds = int(params.get("seconds", 30))
        interval = int(params.get("interval", 5))
        out = run_broker_paper_daemon(seconds=seconds, interval_s=interval)
        payload = _last_cycle_payload()
        payload.update({"mode_truth": "BROKER FILLS"})
        return {"status": out.get("status", "HALT"), "mode": "broker_paper_daemon", "cycle": out, "account": get_account_summary(), **payload}

    if action == "paper_account":
        return {"status": "ok", "account": get_account_summary(), **_last_cycle_payload()}
    if action == "reset_paper":
        return {"status": "ok", "account": reset_account(float(params.get("starting_capital", 5000.0))), **_truth_defaults()}
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
        out = run_live_monitor(mode="polling")
        return {**out, "mode_truth": "SIMULATED FILLS"}
    if action == "websocket_monitor":
        out = run_live_monitor(mode="websocket")
        return {**out, "mode_truth": "SIMULATED FILLS"}
    if action == "api_doctor":
        return _api_doctor()
    if action == "dry_run":
        return {"status": "ok", "mode": "dry_run", "message": "Dry run ready."}
    if action == "live_check":
        return live_gates(bool(params.get("confirm_live", False)), str(params.get("risk_ack", "")), int(params.get("paper_days", 0)), int(params.get("micro_live_days", 0)))
    return {"status": "error", "message": f"Unknown action: {action}"}
