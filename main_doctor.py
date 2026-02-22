from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, 'src')

from omega_quant.ops.repo_guard import ensure_repo_root_or_exit


def run(cmd: list[str]) -> tuple[bool, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", "src")
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
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

    if not report["broker_enabled"]:
        report["ws_health"] = "REQUIRES ALPACA KEYS -> POLLING"
        report["status"] = "WARN"
        report["mode"] = "BROKER DISABLED / USING FALLBACK DATA"
        report["next_action"] = "Set ALPACA_API_KEY/ALPACA_API_SECRET/ALPACA_BASE_URL"
        return report

    ok, out = run([sys.executable, "-c", "from omega_quant.data.providers.alpaca_provider import AlpacaMarketDataProvider;p=AlpacaMarketDataProvider();bars=p.get_bars('SPY','1h',limit=3);print(p.source_name());print(bars[-1].timestamp if bars else '')"])
    if not ok:
        report["errors"].append("bars")
    else:
        lines = [x.strip() for x in out.splitlines() if x.strip()]
        if len(lines) >= 2:
            report["provider_primary"] = lines[0]
            report["last_bar_ts"] = lines[1]
            report["freshness_seconds"] = _freshness(lines[1]) or "unknown"

    report["ws_health"] = "configured"
    report["next_action"] = "Run websocket monitor" if not report["errors"] else "Fix doctor errors"
    report["status"] = "PASS" if not report["errors"] else "WARN"
    report["mode"] = "BROKER ENABLED" if report["status"] == "PASS" else "BROKER DISABLED / USING FALLBACK DATA"
    return report


def main() -> int:
    ensure_repo_root_or_exit("main_doctor.py")
    checks = [
        ("compile", [sys.executable, "-m", "compileall", "-q", "."]),
        ("tests", [sys.executable, "-m", "pytest", "-q"]),
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
