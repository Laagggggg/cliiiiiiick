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
from omega_quant.monitor.live_ws import get_ws_state


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
    saw_q = False
    saw_b = False
    while time.time() - start < args.seconds:
        samples.append(run_live_monitor(mode="websocket"))
        st = get_ws_state()
        saw_q = saw_q or bool(st.get("last_quote_ts"))
        saw_b = saw_b or bool(st.get("last_bar_ts"))
        time.sleep(1)

    last = samples[-1] if samples else {}
    data_grade = str(last.get("data_grade", ""))
    sent = str(last.get("decision_sentence", "")).upper()
    demo_labeled = data_grade in {"CSV_SAMPLE", "CACHED", "DEGRADED_POLLING"} and ("NOT LIVE DATA" in sent or "DEMO" in sent or "WARN:" in sent)
    live_ok = keys_present and ws_lib and data_grade not in {"CSV_SAMPLE", "CACHED", "DEGRADED_POLLING"} and last.get("transport") == "WEBSOCKET" and saw_q and saw_b

    if keys_present and ws_lib:
        status = "PASS" if live_ok else "FAIL"
        reason = "" if live_ok else "live_expected_but_no_ws_q_and_b_events"
    else:
        status = "PASS" if demo_labeled else "FAIL"
        reason = "" if demo_labeled else "demo_not_explicitly_labeled"

    result = {
        "status": status,
        "reason": reason,
        "next_action": "Set Alpaca keys/websocket access and rerun" if status != "PASS" else "None",
        "metrics": {
            "seconds": args.seconds,
            "keys_present": keys_present,
            "websockets_installed": ws_lib,
            "transport": last.get("transport"),
            "data_grade": data_grade,
            "mode_truth": last.get("mode_truth"),
            "freshness_seconds": last.get("freshness_seconds"),
            "decision_sentence": last.get("decision_sentence"),
            "saw_quote": saw_q,
            "saw_bar": saw_b,
        },
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
