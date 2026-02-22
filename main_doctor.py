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
    report: dict = {"env": {}, "errors": []}
    required = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    report["env"] = {k: bool(os.getenv(k)) for k in required}
    report["ws_status"] = "installed" if importlib.util.find_spec("websockets") is not None else "missing_dependency"
    if report["ws_status"] != "installed":
        report["errors"].append("missing_websockets_dependency")

    report["provider_status"] = "not_checked"
    report["broker_status"] = "disabled"
    report["last_bar_ts"] = "not_loaded"
    report["freshness_seconds"] = "not_loaded"

    if not all(report["env"].values()):
        report["status"] = "WARN"
        report["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        report["broker_status"] = "REQUIRES ALPACA KEYS"
        return report

    checks = {
        "account": "python - <<'PY'\nimport sys;sys.path.insert(0,'src')\nfrom omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker\nprint(bool(AlpacaPaperBroker().get_account().get('id')))\nPY",
        "quote": "python - <<'PY'\nimport sys;sys.path.insert(0,'src')\nfrom omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider\np=AlpacaMarketDataProvider();q=p.get_quote('SPY');bars=p.get_bars('SPY','1h',limit=2);print(bool(q), bars[-1].timestamp if bars else '')\nPY",
    }
    for name, cmd in checks.items():
        ok, out = run(cmd)
        report[name] = {"ok": ok, "output": out}
        if not ok:
            report["errors"].append(name)

    quote_output = report.get("quote", {}).get("output", "")
    bits = quote_output.split()
    if len(bits) >= 2:
        report["provider_status"] = "ok" if bits[0] == "True" else "warn"
        report["last_bar_ts"] = bits[1]
        fresh = _freshness(bits[1])
        report["freshness_seconds"] = fresh if fresh is not None else "unknown"

    report["broker_status"] = "ok" if report.get("account", {}).get("ok") else "warn"
    report["status"] = "PASS" if not report["errors"] else "WARN"
    report["mode"] = "BROKER ENABLED" if report["status"] == "PASS" else "BROKER DISABLED / USING FALLBACK DATA"
    return report


def main() -> int:
    checks = [
        ("compile", "python -m py_compile $(rg --files -g '*.py')"),
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
