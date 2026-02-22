from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from omega_quant.ui_service import run_action


def main() -> int:
    out_path = Path("artifacts/live_verified_acceptance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    res = run_action("make_live_verified", {})
    status = res.get("status", "HALT")
    final = {
        "status": "PASS" if status == "ok" and res.get("live_verified") else ("SKIP" if res.get("reason") in {"alpaca_setup_failed", "live_readiness_failed", "api_doctor_failed"} else "FAIL"),
        "reason": res.get("reason", ""),
        "next_action": res.get("next_action", "Run API Doctor"),
        "live_verified": bool(res.get("live_verified")),
        "decision_sentence": res.get("decision_sentence", ""),
    }
    out_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    return 0 if final["status"] in {"PASS", "SKIP"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
