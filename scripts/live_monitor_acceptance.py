from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

from omega_quant.monitor.live_monitor import run_live_monitor


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=int, default=60)
    args = p.parse_args()

    out_path = Path("artifacts/live_monitor_acceptance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    keys_present = bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_API_SECRET"))
    ws_lib = importlib.util.find_spec("websockets") is not None
    samples = []
    start = time.time()
    while time.time() - start < args.seconds:
        samples.append(run_live_monitor(mode="websocket"))
        time.sleep(1)

    last = samples[-1] if samples else {}
    data_grade = str(last.get("data_grade", ""))
    demo_labeled = data_grade in {"CSV_SAMPLE", "CACHED"} and "NOT LIVE DATA" in str(last.get("decision_sentence", "")).upper()
    live_ok = keys_present and ws_lib and data_grade not in {"CSV_SAMPLE", "CACHED"} and last.get("transport") == "WEBSOCKET"

    status = "FAIL"
    reason = ""
    if keys_present and ws_lib:
        status = "PASS" if live_ok else "FAIL"
        reason = "" if live_ok else "live_expected_but_demo_or_not_websocket"
    else:
        status = "PASS" if demo_labeled else "FAIL"
        reason = "" if demo_labeled else "demo_not_explicitly_labeled"

    result = {
        "status": status,
        "reason": reason,
        "metrics": {
            "seconds": args.seconds,
            "keys_present": keys_present,
            "websockets_installed": ws_lib,
            "transport": last.get("transport"),
            "data_grade": data_grade,
            "mode_truth": last.get("mode_truth"),
            "freshness_seconds": last.get("freshness_seconds"),
            "decision_sentence": last.get("decision_sentence"),
        },
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
