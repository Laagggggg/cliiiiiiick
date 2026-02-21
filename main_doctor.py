from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def run(cmd: str) -> tuple[bool, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def api_doctor() -> dict:
    report: dict = {"env": {}, "errors": []}
    required = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    report["env"] = {k: bool(os.getenv(k)) for k in required}

    if not all(report["env"].values()):
        report["status"] = "WARN"
        report["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        return report

    checks = {
        "account": "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.execution.broker.alpaca_paper import AlpacaPaperBroker\nprint(bool(AlpacaPaperBroker().get_account().get('id')))\nPY",
        "quote": "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider\nprint(AlpacaMarketDataProvider().get_quote('SPY') is not None)\nPY",
        "bars_1h": "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider\nprint(len(AlpacaMarketDataProvider().get_bars('SPY','1h',limit=200)))\nPY",
        "ws_probe": "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.monitor.live_ws import run_live_websocket\nprint(run_live_websocket('SPY'))\nPY",
    }
    for name, cmd in checks.items():
        ok, out = run(cmd)
        report[name] = {"ok": ok, "output": out}
        if not ok:
            report["errors"].append(name)

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
