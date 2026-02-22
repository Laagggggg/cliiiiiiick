from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")

from omega_quant.ui_service import run_action


def main() -> int:
    out_path = Path("artifacts/broker_daemon_acceptance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not (os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_API_SECRET")):
        out = run_action("broker_paper_daemon", {"seconds": 5, "interval": 1})
        ok = out.get("status") == "HALT" and bool(out.get("next_action"))
        result = {"status": "PASS" if ok else "FAIL", "reason": "missing_keys_halt_contract", "sample": out}
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0 if ok else 1

    r1 = run_action("broker_paper_daemon", {"seconds": 5, "interval": 1})
    r2 = run_action("broker_paper_daemon", {"seconds": 5, "interval": 1})
    c1 = int(r1.get("cycle", {}).get("placed", 0) or 0)
    c2 = int(r2.get("cycle", {}).get("placed", 0) or 0)
    ok = c2 <= c1
    result = {"status": "PASS" if ok else "FAIL", "reason": "idempotency_double_run", "first": r1, "second": r2}
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
