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
from omega_quant.paper_account.db import get_account_summary, list_trades, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


def default_metrics() -> dict:
    return {"wfe": 0.62, "dsr_confidence": 0.97, "pbo": 0.30, "white_rc_p": 0.03, "spa_p": 0.02, "recovery_factor": 3.4, "expectancy": 0.12}


def _truth_defaults() -> dict:
    return {
        "mode_truth": "DEMO",
        "data_grade": "CSV_SAMPLE",
        "transport": "POLLING",
        "provider_primary": "fallback",
        "provider_secondary": "none",
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "freshness_seconds": None,
        "freshness_label": "N/A (static sample)",
        "last_bar_ts": "unknown -> NEXT ACTION: Run live monitor",
        "next_action": "DEMO DATA (CSV). Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor",
    }


def _last_cycle_payload() -> dict:
    p = Path("artifacts/paper_cycle_result.json")
    if not p.exists():
        return {"last_decision": {"sentence": "NO_TRADE: run historical sim or monitor first"}, **_truth_defaults()}
    data = json.loads(p.read_text(encoding="utf-8"))
    last_reason = data.get("last_decision_reason", "NO_TRADE: no recent fills")
    prov = data.get("provenance", {})
    recon = prov.get("reconciliation", {})
    data_grade = "CSV_SAMPLE" if str(prov.get("source_primary","")).startswith("csv:") else "FALLBACK_POLLING"
    freshness = prov.get("freshness_seconds")
    freshness_label = "N/A (static sample)" if data_grade == "CSV_SAMPLE" else (str(freshness) if freshness is not None else "unknown")
    proof = verify_paper_result()
    return {
        "last_decision": {"sentence": str(last_reason)},
        "provenance": prov,
        "charts": {"equity": "artifacts/equity_curve.png", "drawdown": "artifacts/drawdown.png", "trades": "artifacts/trade_markers.png"},
        "mode_truth": "DEMO" if data_grade == "CSV_SAMPLE" else data.get("mode_truth", "SIMULATED FILLS"),
        "data_grade": data_grade,
        "transport": prov.get("transport", "POLLING"),
        "provider_primary": prov.get("source_primary", "fallback"),
        "provider_secondary": prov.get("source_secondary", "none"),
        "reconciliation": recon,
        "freshness_seconds": freshness,
        "freshness_label": freshness_label,
        "last_bar_ts": prov.get("end", "not loaded (run monitor)"),
        "next_action": "DEMO DATA (CSV). Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor" if data_grade == "CSV_SAMPLE" else "Run live monitor",
        "proof_status": "PASS" if proof.get("ok") else "FAIL",
    }


def _api_doctor() -> dict:
    req = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    env = {k: bool(os.getenv(k)) for k in req}
    broker = AlpacaPaperBroker()
    out = {
        "env": env,
        "ws_available": False,
        "ws_health": "unknown",
        "provider_primary": "unknown",
        "provider_secondary": "none",
        "broker_enabled": broker.enabled(),
        "last_bar_ts": "unknown",
        "freshness_seconds": "unknown",
        "next_action": "DEMO DATA (CSV). Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor",
        "errors": [],
    }

    try:
        import importlib.util
        out["ws_available"] = importlib.util.find_spec("websockets") is not None
    except Exception:  # noqa: BLE001
        out["ws_available"] = False

    if not broker.enabled():
        out["ws_health"] = "REQUIRES ALPACA KEYS -> POLLING"
        out["status"] = "WARN"
        out["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        out["next_action"] = "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL"
        return out

    out["ws_health"] = "configured"
    try:
        acct = broker.get_account()
        out["account"] = {"id": acct.get("id"), "status": acct.get("status")}
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"account:{exc}")

    try:
        from datetime import datetime, timezone
        from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider

        prov = AlpacaMarketDataProvider()
        bars = prov.get_bars("SPY", "1h", limit=100)
        out["provider_primary"] = prov.source_name()
        out["provider_secondary"] = "fallback"
        if bars:
            out["last_bar_ts"] = bars[-1].timestamp
            dt = datetime.fromisoformat(bars[-1].timestamp.replace("Z", "+00:00"))
            out["freshness_seconds"] = int((datetime.now(timezone.utc) - dt).total_seconds())
            out["next_action"] = "Run websocket monitor"
        else:
            out["errors"].append("no_bars")
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"data:{exc}")

    out["status"] = "PASS" if not out["errors"] else "WARN"
    out["mode"] = "BROKER ENABLED" if out["status"] == "PASS" else "BROKER DISABLED / USING FALLBACK DATA"
    return out




def _paper_decision_sentence(cycle: dict) -> str:
    res = cycle.get("result", {})
    trades = int(res.get("session_trade_count", 0))
    pnl = float(res.get("session_pnl_dollars", 0.0))
    cap = float(res.get("starting_capital", 0.0))
    if trades > 0:
        pct = (pnl / cap * 100.0) if cap else 0.0
        return f"TRADE: session_pnl=${pnl:.2f} ({pct:.2f}%) over {trades} trades"
    return "NO_TRADE: score<threshold or guards blocked entry"



def _wizard_run(starting_capital: float, cycles: int) -> dict:
    path = Path('artifacts/wizard_run.json')
    if path.exists():
        try:
            state = json.loads(path.read_text(encoding='utf-8'))
        except Exception:  # noqa: BLE001
            state = {"steps": []}
    else:
        state = {"steps": []}

    done = {x.get('step'): x for x in state.get('steps', []) if x.get('status') == 'ok'}

    def step(name: str, action: str, params: dict | None = None) -> dict:
        if name in done:
            return done[name]
        out = run_action(action, params or {})
        rec = {"step": name, "status": "ok" if out.get('status') in {'ok', 'PASS'} else 'HALT', "output": out}
        state.setdefault('steps', []).append(rec)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding='utf-8')
        return rec

    ordered = [
        ('doctor', 'api_doctor', {}),
        ('reset_paper', 'reset_paper', {'starting_capital': starting_capital}),
        ('paper', 'paper', {'starting_capital': starting_capital, 'cycles': cycles}),
        ('proof_check', 'proof_check', {}),
        ('download_audit_pack', 'download_audit_pack', {}),
    ]

    results = []
    for name, action, params in ordered:
        r = step(name, action, params)
        results.append(r)
        if r['status'] != 'ok':
            return {
                'status': 'HALT',
                'mode': 'wizard',
                'steps': results,
                'decision_sentence': f"HALT: wizard step={name} failed; NEXT_ACTION={r['output'].get('next_action','inspect output')}",
                'next_action': r['output'].get('next_action', 'inspect output'),
            }

    summary = _last_cycle_payload()
    proof_status = next((x['output'].get('status') for x in results if x['step']=='proof_check'), 'HALT')
    audit_status = next((x['output'].get('status') for x in results if x['step']=='download_audit_pack'), 'error')
    return {
        'status': 'ok',
        'mode': 'wizard',
        'steps': results,
        'decision_sentence': 'TRADE: wizard completed all safety/proof steps',
        'data_grade': summary.get('data_grade','CSV_SAMPLE'),
        'transport': summary.get('transport','POLLING'),
        'last_bar_ts': summary.get('last_bar_ts','unknown'),
        'freshness_label': summary.get('freshness_label','N/A (static sample)'),
        'proof_status': proof_status,
        'audit_pack_status': audit_status,
        'next_action': summary.get('next_action','Optional: configure Alpaca keys'),
    }

def run_action(action: str, params: dict | None = None) -> dict:
    params = params or {}
    metrics = default_metrics()

    if action == "validate":
        return master_validation(metrics, [1, 2, 3, 4, 5], [1.1, 2.1, 3.0, 3.9, 5.2])

    if action == "wizard_run":
        cap = float(params.get("starting_capital", 5000.0))
        cyc = int(params.get("cycles", 1))
        return _wizard_run(cap, cyc)
    if action == "report":
        return {"research_report": render_report(metrics), "checklist": render_go_no_go_markdown(metrics)}

    if action == "paper":
        prior = verify_paper_result()
        if prior.get("exists") and not prior.get("ok"):
            return {"status": "HALT", "reason": "proof_failed_block", "proof": prior}
        from omega_quant.ops.paper_cycle import run_paper_cycle

        out = run_paper_cycle(starting_capital=float(params.get("starting_capital", 5000.0)), cycles=int(params.get("cycles", 1)))
        proof = verify_paper_result()
        sentence = _paper_decision_sentence(out)
        return {"status": "ok" if proof.get("ok") else "HALT", "mode": "paper", "cycle": out, "proof": proof, "decision_sentence": sentence, "account": get_account_summary(), **_last_cycle_payload()}

    if action == "broker_paper_run":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, **_truth_defaults()}
        steps = int(params.get("steps", 1))
        out = run_broker_paper_cycle(steps=steps)
        payload = _last_cycle_payload()
        payload.update({"mode_truth": "BROKER FILLS"})
        sentence = out.get("decision_sentence") or f"{out.get('status','HALT')}: broker paper step completed"
        return {"status": out.get("status", "HALT"), "mode": "broker_paper", "cycle": out, "decision_sentence": sentence, "account": get_account_summary(), **payload}

    if action == "broker_paper_daemon":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return {"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, **_truth_defaults()}
        seconds = int(params.get("seconds", 30))
        interval = int(params.get("interval", 5))
        out = run_broker_paper_daemon(seconds=seconds, interval_s=interval)
        payload = _last_cycle_payload()
        payload.update({"mode_truth": "BROKER FILLS"})
        sentence = out.get("decision_sentence") or f"{out.get('status','HALT')}: broker daemon run completed"
        return {"status": out.get("status", "HALT"), "mode": "broker_paper_daemon", "cycle": out, "decision_sentence": sentence, "account": get_account_summary(), **payload}

    if action == "paper_account":
        acct = get_account_summary()
        tr = list_trades()[-20:]
        return {"status": "ok", "account": acct, "last_trades": tr, **_last_cycle_payload()}
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
        return {**out, "provider_primary": out.get("source", "fallback"), "provider_secondary": out.get("source_secondary", "none")}
    if action == "websocket_monitor":
        out = run_live_monitor(mode="websocket")
        if "REQUIRES ALPACA KEYS" in str(out.get("transport", "")):
            out["status"] = "HALT"
            out["decision_sentence"] = "HALT: missing Alpaca keys; set environment vars and rerun doctor"
            out["next_action"] = 'PowerShell: $env:ALPACA_API_KEY="..."; $env:ALPACA_API_SECRET="..."; $env:ALPACA_BASE_URL="https://paper-api.alpaca.markets"; python main_doctor.py'
        return {**out, "provider_primary": out.get("source", "fallback"), "provider_secondary": out.get("source_secondary", "none")}
    if action == "replay_live_stream":
        from omega_quant.monitor.live_ws import replay_stream
        out = replay_stream()
        return {**out, "mode_truth": "LIVE_MONITOR_DEMO"}
    if action == "api_doctor":
        return _api_doctor()
    if action == "dry_run":
        return {"status": "ok", "mode": "dry_run", "message": "Dry run ready."}
    if action == "live_check":
        return live_gates(bool(params.get("confirm_live", False)), str(params.get("risk_ack", "")), int(params.get("paper_days", 0)), int(params.get("micro_live_days", 0)))
    return {"status": "error", "message": f"Unknown action: {action}"}
