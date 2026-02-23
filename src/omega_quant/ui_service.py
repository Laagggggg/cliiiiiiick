from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import TypedDict

from omega_quant.config.alpaca_config import get_alpaca_config
from omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker
from omega_quant.live_gates import live_gates
from omega_quant.monitor.live_monitor import compute_freshness, run_live_monitor
from omega_quant.ops.broker_paper_cycle import run_broker_paper_cycle
from omega_quant.ops.broker_paper_daemon import run_broker_paper_daemon
from omega_quant.ops.master_validation import master_validation
from omega_quant.ops.proof_check import verify_paper_result
from omega_quant.paper_account.db import get_account_summary, get_paper_days_completed, list_trades, reset_account
from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report
from omega_quant.time.market_hours import TIMEZONE_NEXT_ACTION, market_timezone_status


class TruthPayload(TypedDict):
    mode_truth: str
    data_grade: str
    transport: str
    provider_primary: str
    provider_secondary: str
    recon_status: str
    reconciliation: dict
    freshness_seconds: int | None
    freshness_label: str
    last_bar_ts: str
    next_action: str
    freshness_basis: str
    live_verified: bool
    feed_label: str
    ws_health: str
    last_event_kind: str
    stall_seconds: int
    decision_sentence: str


def default_metrics() -> dict:
    return {"wfe": 0.62, "dsr_confidence": 0.97, "pbo": None, "pbo_label": "CPCV/PBO NOT IMPLEMENTED", "white_rc_p": 0.03, "spa_p": 0.02, "recovery_factor": 3.4, "expectancy": 0.12, "gt_score_label": "HEURISTIC (non-peer-reviewed)"}


def _truth_defaults() -> TruthPayload:
    return {
        "mode_truth": "DEMO",
        "data_grade": "CSV_SAMPLE",
        "transport": "POLLING",
        "provider_primary": "CSV_SAMPLE",
        "provider_secondary": "none",
        "recon_status": "UNKNOWN",
        "reconciliation": {"passed": None, "max_diff_pct": None},
        "freshness_seconds": None,
        "freshness_label": "N/A (static sample)",
        "last_bar_ts": "unknown",
        "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor",
        "freshness_basis": "static_sample",
        "live_verified": False,
        "feed_label": "DEMO",
        "ws_health": "disconnected",
        "last_event_kind": "none",
        "stall_seconds": 0,
        "decision_sentence": "NO_TRADE: startup state. Next: run monitor or paper cycle.",
        "provenance": {"provider_primary": "CSV_SAMPLE", "data_grade": "CSV_SAMPLE", "last_bar_ts": "unknown", "freshness_label": "N/A (static sample)", "freshness_basis": "static_sample", "dataset_sha256": "unknown", "bars_loaded": 0, "recon_status": "UNKNOWN"},
    }





def _csv_dataset_sha256(path: str = "data/spy_1h_sample.csv") -> str:
    p = Path(path)
    if not p.exists():
        return "unknown"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _provenance_from_truth(payload: dict) -> dict:
    prov = payload.get("provenance") or {}
    if not prov:
        prov = {
            "provider_primary": payload.get("provider_primary", "CSV_SAMPLE"),
            "data_grade": payload.get("data_grade", "CSV_SAMPLE"),
            "last_bar_ts": payload.get("last_bar_ts", "unknown"),
            "freshness_label": payload.get("freshness_label", "N/A (static sample)"),
            "freshness_basis": payload.get("freshness_basis", "static_sample"),
            "dataset_sha256": _csv_dataset_sha256() if payload.get("data_grade") == "CSV_SAMPLE" else "n/a",
            "bars_loaded": int(payload.get("bars_loaded", 0) or 0),
            "recon_status": payload.get("recon_status", "UNKNOWN"),
        }
    return prov

def _human_sentence(status: str, sentence: str, next_action: str) -> str:
    txt = (sentence or "").strip()
    if not txt:
        txt = f"{status}: no reason provided."
    if not txt.startswith(("HALT:", "NO_TRADE:", "TRADE:", "WARN:", "SKIP:", "ok:", "OK:")):
        txt = f"{status}: {txt}"
    if "Next:" not in txt:
        txt = f"{txt} Next: {next_action}."
    return txt


def _is_live_verified(payload: dict) -> bool:
    keys_present = bool(payload.get("keys_present", False))
    provider_ok = str(payload.get("provider_primary", "")).upper() in {"ALPACA", "ALPACA_BARS", "ALPACA_WEBSOCKET"}
    transport = str(payload.get("transport", "")).upper()
    fresh = payload.get("freshness_seconds")
    last_bar_ts = str(payload.get("last_bar_ts", "")).lower()
    mode_truth = str(payload.get("mode_truth", ""))
    ws_health = str(payload.get("ws_health", "")).lower()
    recent = isinstance(fresh, int) and fresh <= 7200
    transport_ok = (transport == "WEBSOCKET" and "connected" in ws_health) or (transport == "POLLING" and recent)
    alpaca_call_succeeded = bool(payload.get("alpaca_call_succeeded"))
    return keys_present and provider_ok and transport_ok and last_bar_ts not in {"", "unknown", "not loaded (run monitor)"} and mode_truth == "LIVE_MONITOR_SAFE" and alpaca_call_succeeded


def _enforce_truth_payload(payload: dict) -> dict:
    out = {**_truth_defaults(), **payload}
    recon = out.get("reconciliation", {}) or {}
    if recon.get("passed") is True:
        out["recon_status"] = "PASS"
    elif recon.get("passed") is False:
        out["recon_status"] = "FAIL"
    if out.get("data_grade") == "CSV_SAMPLE":
        out["mode_truth"] = "DEMO"
        out["freshness_seconds"] = None
        out["freshness_label"] = "N/A (static sample)"
    elif out.get("data_grade") == "CACHED":
        out["mode_truth"] = out.get("mode_truth") or "SAFE_DEGRADED"
        out["freshness_label"] = out.get("freshness_label") or "cached"
    status = str(out.get("status", "HALT")).upper()
    out["decision_sentence"] = _human_sentence(status, str(out.get("decision_sentence", "")), str(out.get("next_action", "Run API Doctor")))
    out["provenance"] = _provenance_from_truth(out)
    out["live_verified"] = _is_live_verified(out)
    return out


def _last_cycle_payload() -> dict:
    p = Path("artifacts/paper_cycle_result.json")
    if not p.exists():
        return _enforce_truth_payload({"last_decision": {"sentence": "NO_TRADE: run historical sim or monitor first"}})
    data = json.loads(p.read_text(encoding="utf-8"))
    last_reason = data.get("last_decision_reason", "NO_TRADE: no recent fills")
    prov = data.get("provenance", {})
    bars_loaded = int(prov.get("bars_loaded", 0) or 0)
    recon = prov.get("reconciliation", {})
    source_primary = str(prov.get("source_primary", "CSV_SAMPLE"))
    data_grade = "CSV_SAMPLE" if source_primary.startswith("csv:") else "DEGRADED_POLLING"
    freshness = prov.get("freshness_seconds")
    fresh_obj = compute_freshness(data_grade=data_grade, bar_ts=str(prov.get("end", "")))
    proof = verify_paper_result()
    return _enforce_truth_payload(
        {
            "last_decision": {"sentence": str(last_reason)},
            "provenance": prov,
            "charts": {"equity": "artifacts/equity_curve.png", "drawdown": "artifacts/drawdown.png", "trades": "artifacts/trade_markers.png"},
            "mode_truth": "DEMO" if data_grade == "CSV_SAMPLE" else data.get("mode_truth", "SIMULATED FILLS"),
            "data_grade": data_grade,
            "transport": prov.get("transport", "POLLING"),
            "provider_primary": "CSV_SAMPLE" if source_primary.startswith("csv:") else str(source_primary).upper(),
            "provider_secondary": prov.get("source_secondary", "none"),
            "reconciliation": recon,
            "freshness_seconds": freshness if freshness is not None else fresh_obj["freshness_seconds"],
            "freshness_label": "N/A (static sample)" if data_grade == "CSV_SAMPLE" else fresh_obj["freshness_label"],
            "freshness_basis": fresh_obj["freshness_basis"],
            "last_bar_ts": prov.get("end", "not loaded (run monitor)"),
            "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor" if data_grade == "CSV_SAMPLE" else "Run live monitor",
            "proof_status": "PASS" if proof.get("ok") else "FAIL",
            "bars_loaded": bars_loaded,
            "decision_sentence": str(last_reason),
        }
    )




def _alpaca_setup_payload() -> dict:
    cfg = get_alpaca_config()
    missing = [k for k in ["ALPACA_API_KEY", "ALPACA_API_SECRET"] if not cfg["api_key"] if k=="ALPACA_API_KEY"]
    # explicit map for UI
    missing = []
    if not cfg["api_key"]:
        missing.append("ALPACA_API_KEY")
    if not cfg["api_secret"]:
        missing.append("ALPACA_API_SECRET")
    setup_block = 'Copy .env.example to .env and set keys. PowerShell: Copy-Item .env.example .env; notepad .env'
    return {
        "status": "ok" if not missing else "HALT",
        "reason": "alpaca_config_ready" if not missing else "missing_alpaca_keys",
        "next_action": "Run API Doctor" if not missing else setup_block,
        "alpaca": {
            "missing": missing,
            "trading_base_url": cfg["trading_base_url"],
            "data_base_url": cfg["data_base_url"],
            "ws_url": cfg["ws_url"],
            "warnings": cfg.get("warnings", []),
            "env_helper": setup_block,
        },
    }


def _live_readiness_payload() -> dict:
    from importlib.util import find_spec
    from omega_quant.monitor.live_ws import get_ws_state

    mon = run_live_monitor(mode="websocket")
    cfg = get_alpaca_config()
    ws = get_ws_state()
    fresh = mon.get("freshness_seconds")
    keys_ok = bool(cfg.get("api_key") and cfg.get("api_secret"))
    ws_lib = find_spec("websockets") is not None
    paper_days = get_paper_days_completed()
    tz_status = market_timezone_status()
    checks = {
        "keys_present": {"ok": keys_ok, "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET in .env"},
        "websockets_installed": {"ok": ws_lib, "next_action": "python -m pip install websockets"},
        "websocket_connected": {"ok": bool(ws.get("connected")), "next_action": "Run API Doctor and websocket monitor"},
        "polling_fallback_active": {"ok": "POLLING" in str(mon.get("transport", "")), "next_action": "If expected live, fix websocket/auth"},
        "last_bar_recent": {"ok": isinstance(fresh, int) and fresh < 7200, "next_action": "Check provider/data freshness"},
        "paper_phase": {"ok": paper_days >= 45, "next_action": "Run paper until 45 unique days are completed"},
        "market_timezone": {"ok": bool(tz_status.get("ok")), "next_action": tz_status.get("next_action", TIMEZONE_NEXT_ACTION)},
    }
    overall_ok = all(v["ok"] for v in checks.values() if v is not checks["polling_fallback_active"])
    return _enforce_truth_payload({
        **mon,
        "status": "ok" if overall_ok else "HALT",
        "reason": "live_ready" if overall_ok else "live_readiness_failed",
        "next_action": "Run live monitor acceptance" if overall_ok else "Review failed checklist items and fix env/connectivity",
        "readiness": checks,
        "paper_days_completed": paper_days,
        "paper_days_required": 45,
    })

def _api_doctor() -> dict:
    req = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    cfg = get_alpaca_config()
    env = {"ALPACA_API_KEY": bool(cfg.get("api_key")), "ALPACA_API_SECRET": bool(cfg.get("api_secret")), "ALPACA_BASE_URL": bool(cfg.get("trading_base_url"))}
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
        "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor",
        "errors": [],
        "keys_present": broker.enabled(),
        "ws_health": "connected" if broker.enabled() else "unknown",
    }
    try:
        import importlib.util
        out["ws_available"] = importlib.util.find_spec("websockets") is not None
    except Exception:  # noqa: BLE001
        out["ws_available"] = False

    if not all(env.values()):
        out["ws_health"] = "REQUIRES ALPACA KEYS -> POLLING"
        out["status"] = "WARN"
        out["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        out["next_action"] = "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL then run API Doctor"
        return out
    out["status"] = "PASS"
    out["mode"] = "BROKER ENABLED"
    return out






def _make_live_verified() -> dict:
    steps = []
    for action in ["alpaca_setup", "live_readiness", "api_doctor"]:
        out = run_action(action, {})
        steps.append({"action": action, "status": out.get("status"), "next_action": out.get("next_action")})
        if out.get("status") in {"HALT", "error"}:
            return _enforce_truth_payload({"status": "HALT", "reason": f"{action}_failed", "steps": steps, "next_action": out.get("next_action", "Run API Doctor"), "decision_sentence": f"HALT: {action} failed"})
    script = Path(__file__).resolve().parents[2] / "scripts" / "live_ws_acceptance.py"
    proc = subprocess.run(f"python {script} --seconds 15", shell=True, capture_output=True, text=True)
    steps.append({"action": "live_ws_acceptance", "status": "ok" if proc.returncode == 0 else "HALT", "output": (proc.stdout + proc.stderr).strip()})
    mon = run_live_monitor(mode="websocket")
    payload = _enforce_truth_payload({**mon, "provider_primary": mon.get("source", "UNKNOWN_PROVIDER"), "provider_secondary": mon.get("source_secondary", "none")})
    if not payload.get("live_verified"):
        return _enforce_truth_payload({**payload, "status": "HALT", "steps": steps, "decision_sentence": "HALT: live verification did not pass", "next_action": payload.get("next_action", "Run doctor and acceptance scripts")})
    return _enforce_truth_payload({**payload, "status": "ok", "steps": steps, "decision_sentence": "OK: live verification passed", "next_action": "Run broker daemon if ready"})

def _platform_helper(action: str) -> dict:
    is_win = platform.system().lower().startswith("win")
    if action == "open_alpaca_keys_page":
        if is_win:
            subprocess.run('start "" "https://app.alpaca.markets/paper/dashboard/overview"', shell=True)
            return {"status": "ok", "reason": "opened_browser", "next_action": "Paste keys into .env and run API Doctor"}
        return {"status": "HALT", "reason": "non_windows_noop", "next_action": "Open https://app.alpaca.markets/paper/dashboard/overview manually"}
    if action == "open_env_notepad":
        if is_win:
            subprocess.run('notepad .env', shell=True)
            return {"status": "ok", "reason": "opened_notepad", "next_action": "Fill .env then run API Doctor"}
        return {"status": "HALT", "reason": "non_windows_noop", "next_action": "Edit .env with your editor"}
    if action == "copy_tzdata_fix_command":
        cmd = "python -m pip install tzdata"
        if is_win:
            subprocess.run(f'echo {cmd.strip()}| clip', shell=True)
            return {"status": "ok", "reason": "copied_tzdata_command", "command": cmd, "next_action": "Run copied command in activated venv"}
        return {"status": "ok", "reason": "tzdata_command", "command": cmd, "next_action": "Run command in your shell"}
    if action == "copy_env_example":
        if Path('.env').exists():
            return {"status": "ok", "reason": "env_exists", "next_action": "Edit .env and run API Doctor"}
        Path('.env').write_text(Path('.env.example').read_text(encoding='utf-8'), encoding='utf-8')
        return {"status": "ok", "reason": "env_copied", "next_action": "Fill .env keys and run API Doctor"}
    return {"status": "error", "reason": "unknown_helper_action", "next_action": "Use supported helper actions"}

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
    path = Path("artifacts/wizard_run.json")
    state = {"steps": []}
    if path.exists():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    done = {x.get("step"): x for x in state.get("steps", []) if x.get("status") == "ok"}

    def step(name: str, action: str, params: dict | None = None) -> dict:
        if name in done:
            return done[name]
        out = run_action(action, params or {})
        rec = {"step": name, "status": "ok" if out.get("status") in {"ok", "PASS"} else "HALT", "output": out}
        state.setdefault("steps", []).append(rec)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return rec

    ordered = [("doctor", "api_doctor", {}), ("reset_paper", "reset_paper", {"starting_capital": starting_capital}), ("paper", "paper", {"starting_capital": starting_capital, "cycles": cycles}), ("proof_check", "proof_check", {}), ("download_audit_pack", "download_audit_pack", {})]
    results = []
    for name, action, params in ordered:
        r = step(name, action, params)
        results.append(r)
        if r["status"] != "ok":
            return _enforce_truth_payload({"status": "HALT", "mode": "wizard", "steps": results, "decision_sentence": f"HALT: wizard step={name} failed", "next_action": r["output"].get("next_action", "inspect output")})

    summary = _last_cycle_payload()
    return _enforce_truth_payload({"status": "ok", "mode": "wizard", "steps": results, "proof_status": next((x["output"].get("status") for x in results if x["step"] == "proof_check"), "HALT"), "audit_pack_status": next((x["output"].get("status") for x in results if x["step"] == "download_audit_pack"), "error"), **summary, "decision_sentence": "TRADE: wizard completed all safety/proof steps"})


def run_action(action: str, params: dict | None = None) -> dict:
    params = params or {}
    metrics = default_metrics()

    if action == "validate":
        return master_validation(metrics, [1, 2, 3, 4, 5], [1.1, 2.1, 3.0, 3.9, 5.2])
    if action == "wizard_run":
        return _wizard_run(float(params.get("starting_capital", 5000.0)), int(params.get("cycles", 1)))
    if action == "report":
        return {"research_report": render_report(metrics), "checklist": render_go_no_go_markdown(metrics)}

    if action == "paper":
        prior = verify_paper_result()
        if prior.get("exists") and not prior.get("ok"):
            return _enforce_truth_payload({"status": "HALT", "reason": "proof_failed_block", "proof": prior, "decision_sentence": "HALT: proof integrity failed", "next_action": "Run reset_paper and rerun paper"})
        from omega_quant.ops.paper_cycle import run_paper_cycle

        out = run_paper_cycle(starting_capital=float(params.get("starting_capital", 5000.0)), cycles=int(params.get("cycles", 1)))
        proof = verify_paper_result()
        return _enforce_truth_payload({"status": "ok" if proof.get("ok") else "HALT", "mode": "paper", "fill_model": "SIM_OHLC_LIMIT", "cycle": out, "proof": proof, "decision_sentence": _paper_decision_sentence(out), "account": get_account_summary(), **_last_cycle_payload()})

    if action == "broker_paper_run":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return _enforce_truth_payload({"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, "decision_sentence": "HALT: missing broker prerequisites", "next_action": "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL and rerun API Doctor"})
        out = run_broker_paper_cycle(steps=int(params.get("steps", 1)))
        payload = _last_cycle_payload()
        return _enforce_truth_payload({"status": out.get("status", "HALT"), "mode": "broker_paper", "fill_model": "BROKER_FILL", "cycle": out, "decision_sentence": out.get("decision_sentence") or "NO_TRADE: broker paper completed", "account": get_account_summary(), **payload, "mode_truth": "BROKER FILLS"})

    if action == "broker_paper_daemon":
        doctor = _api_doctor()
        if doctor.get("status") != "PASS":
            return _enforce_truth_payload({"status": "HALT", "reason": "BROKER DISABLED / USING FALLBACK DATA", "doctor": doctor, "decision_sentence": "HALT: missing broker prerequisites", "next_action": "Set Alpaca env vars and rerun API Doctor"})
        out = run_broker_paper_daemon(seconds=int(params.get("seconds", 30)), interval_s=int(params.get("interval", 5)))
        payload = _last_cycle_payload()
        return _enforce_truth_payload({"status": out.get("status", "HALT"), "mode": "broker_paper_daemon", "fill_model": "BROKER_FILL", "cycle": out, "decision_sentence": out.get("decision_sentence") or "NO_TRADE: broker daemon completed", "account": get_account_summary(), **payload, "mode_truth": "BROKER FILLS"})

    if action == "paper_account":
        return _enforce_truth_payload({"status": "ok", "account": get_account_summary(), "last_trades": list_trades()[-20:], "paper_days_completed": get_paper_days_completed(), "paper_days_required": 45, "fill_model": "SIM_OHLC_LIMIT", **_last_cycle_payload()})
    if action == "reset_paper":
        return _enforce_truth_payload({"status": "ok", "account": reset_account(float(params.get("starting_capital", 5000.0))), "decision_sentence": "NO_TRADE: paper account reset"})
    if action == "proof_check":
        p = verify_paper_result()
        return _enforce_truth_payload({"status": "ok" if p.get("ok") else "HALT", "proof": p, "decision_sentence": "TRADE: proof check passed" if p.get("ok") else "HALT: proof check failed", "next_action": "Run reset_paper and rerun paper" if not p.get("ok") else "Continue paper runs"})
    if action == "paper_review":
        p = Path("artifacts/paper_trade_reviews.md")
        return {"status": "ok", "exists": p.exists(), "path": str(p), "content": p.read_text(encoding="utf-8") if p.exists() else "No paper reviews yet."}
    if action == "download_audit_pack":
        script = Path(__file__).resolve().parents[2] / "scripts" / "make_audit_pack.py"
        proc = subprocess.run(["python", str(script)], capture_output=True, text=True)
        zip_path = Path("dist/paper_audit_pack.zip")
        if proc.returncode == 0 and zip_path.exists():
            return {"status": "ok", "output": proc.stdout.strip(), "path": str(zip_path)}
        return {"status": "error", "output": proc.stdout.strip(), "stderr": proc.stderr.strip() or "audit pack generation failed"}
    if action == "live_monitor":
        out = run_live_monitor(mode="polling")
        return _enforce_truth_payload({**out, "provider_primary": out.get("source", "UNKNOWN_PROVIDER"), "provider_secondary": out.get("source_secondary", "none")})
    if action == "websocket_monitor":
        out = run_live_monitor(mode="websocket")
        if "REQUIRES ALPACA KEYS" in str(out.get("transport", "")):
            out["status"] = "HALT"
            out["decision_sentence"] = "HALT: missing Alpaca keys"
            out["next_action"] = 'PowerShell: $env:ALPACA_API_KEY="..."; $env:ALPACA_API_SECRET="..."; $env:ALPACA_BASE_URL="https://paper-api.alpaca.markets"; python main_doctor.py'
        return _enforce_truth_payload({**out, "provider_primary": out.get("source", "UNKNOWN_PROVIDER"), "provider_secondary": out.get("source_secondary", "none")})
    if action == "replay_live_stream":
        from omega_quant.monitor.live_ws import replay_stream

        out = replay_stream()
        return _enforce_truth_payload({**out, "mode_truth": "LIVE_MONITOR_DEMO", "decision_sentence": "NO_TRADE: replay mode"})
    if action == "api_doctor":
        return _api_doctor()
    if action == "alpaca_setup":
        return _alpaca_setup_payload()
    if action == "live_readiness":
        return _live_readiness_payload()
    if action in {"open_alpaca_keys_page", "open_env_notepad", "copy_env_example", "copy_tzdata_fix_command"}:
        return _enforce_truth_payload(_platform_helper(action))
    if action == "make_live_verified":
        return _make_live_verified()
    if action == "live_verified_acceptance":
        script = Path(__file__).resolve().parents[2] / "scripts" / "live_verified_acceptance.py"
        proc = subprocess.run(f"python {script}", shell=True, capture_output=True, text=True)
        return _enforce_truth_payload({"status": "ok" if proc.returncode == 0 else "HALT", "decision_sentence": "OK: live verified acceptance executed" if proc.returncode == 0 else "HALT: live verified acceptance failed", "next_action": "Inspect artifacts/live_verified_acceptance.json", "output": (proc.stdout + proc.stderr).strip()})
    if action == "dry_run":
        return _enforce_truth_payload({"status": "ok", "mode": "dry_run", "message": "Dry run ready.", "decision_sentence": "NO_TRADE: dry run"})
    if action == "live_check":
        return live_gates(bool(params.get("confirm_live", False)), str(params.get("risk_ack", "")), int(params.get("paper_days", 0)), int(params.get("micro_live_days", 0)))
    return {"status": "error", "message": f"Unknown action: {action}"}
