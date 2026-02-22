from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: str) -> tuple[bool, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def _freshness(ts: str) -> int | None:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:  # noqa: BLE001
        return None


def api_doctor() -> dict:
    report: dict = {
        "env": {},
        "errors": [],
        "ws_available": importlib.util.find_spec("websockets") is not None,
        "ws_health": "unknown",
        "provider_primary": "unknown",
        "provider_secondary": "none",
        "broker_enabled": False,
        "last_bar_ts": "unknown",
        "freshness_seconds": "unknown",
        "next_action": "Run API Doctor",
    }

    required = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    report["env"] = {k: bool(os.getenv(k)) for k in required}
    report["broker_enabled"] = all(report["env"].values())

    # Windows-fragile command lint guard
    fragile_hits: list[str] = []
    for fp in Path('.').glob('*.md'):
        txt = fp.read_text(encoding='utf-8', errors='ignore')
        if '$(rg --files' in txt or '$(' in txt and 'powershell' in fp.name.lower():
            fragile_hits.append(str(fp))
    for fp in Path('.').glob('*.ps1'):
        txt = fp.read_text(encoding='utf-8', errors='ignore')
        if '$(rg --files' in txt:
            fragile_hits.append(str(fp))
    if fragile_hits:
        report['errors'].append('windows_fragile_command_docs')
        report['fragile_command_files'] = fragile_hits

    if not report["ws_available"]:
        report["errors"].append("missing_websockets_dependency")

    if not report["broker_enabled"]:
        report["ws_health"] = "REQUIRES ALPACA KEYS -> POLLING"
        report["status"] = "WARN"
        report["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        report["next_action"] = "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL"
        return report

    checks = {
        "account": "python - <<'PY'\nimport sys;sys.path.insert(0,'src')\nfrom omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker\nprint(bool(AlpacaPaperBroker().get_account().get('id')))\nPY",
        "bars": "python - <<'PY'\nimport sys;sys.path.insert(0,'src')\nfrom omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider\np=AlpacaMarketDataProvider();bars=p.get_bars('SPY','1h',limit=3);print(p.source_name());print(bars[-1].timestamp if bars else '')\nPY",
    }

    for name, cmd in checks.items():
        ok, out = run(cmd)
        report[name] = {"ok": ok, "output": out}
        if not ok:
            report["errors"].append(name)

    if report.get("bars", {}).get("ok"):
        lines = [x.strip() for x in report["bars"]["output"].splitlines() if x.strip()]
        if len(lines) >= 2:
            report["provider_primary"] = lines[0]
            report["provider_secondary"] = "fallback"
            report["last_bar_ts"] = lines[1]
            fresh = _freshness(lines[1])
            report["freshness_seconds"] = fresh if fresh is not None else "unknown"

    report["ws_health"] = "configured" if report["ws_available"] else "missing_dependency"
    report["next_action"] = "Run websocket monitor" if not report["errors"] else "Fix doctor errors"
    report["status"] = "PASS" if not report["errors"] else "WARN"
    report["mode"] = "BROKER ENABLED" if report["status"] == "PASS" else "BROKER DISABLED / USING FALLBACK DATA"
    return report


def main() -> int:
    checks = [
        ("compile", "python -m compileall -q ."),
        ("tests", "pytest -q"),
        ("paper", "PYTHONPATH=src python main_paper.py --capital 3000 --cycles 1"),
    ]
    ok_all = True
    for name, cmd in checks:
        ok, out = run(cmd)
        print(f"[{name}] {'PASS' if ok else 'FAIL'}")
        print(out)
        print('-' * 60)
        ok_all = ok_all and ok

    report = api_doctor()
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/doctor_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[api_doctor]", report.get("status"))
    print(json.dumps(report, indent=2))
    print('-' * 60)

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
