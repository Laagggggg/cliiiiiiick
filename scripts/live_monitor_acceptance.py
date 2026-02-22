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
    result = {"status": "FAIL", "reason": "", "metrics": {}}

    req = ["ALPACA_API_KEY", "ALPACA_API_SECRET", "ALPACA_BASE_URL"]
    missing = [k for k in req if not os.getenv(k)]
    if missing:
        result["reason"] = f"missing_env:{','.join(missing)}"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 1

    if importlib.util.find_spec("websockets") is None:
        result["reason"] = "missing_websockets"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 1

    events_before = get_ws_state()
    started = time.time()
    sample = []
    while time.time() - started < args.seconds:
        mon = run_live_monitor(mode="websocket")
        sample.append(mon)
        time.sleep(1)

    st = get_ws_state()
    event_count = int(bool(st.get("last_quote_ts"))) + int(bool(st.get("last_trade_ts"))) + int(bool(st.get("last_bar_ts")))
    freshness = sample[-1].get("freshness_seconds") if sample else None
    pass_ok = event_count > 0 and isinstance(freshness, int) and freshness < 7200

    result = {
        "status": "PASS" if pass_ok else "FAIL",
        "reason": "" if pass_ok else "no_events_or_stale",
        "metrics": {
            "seconds": args.seconds,
            "event_count": event_count,
            "freshness_seconds": freshness,
            "transport": sample[-1].get("transport") if sample else "",
            "ws_state_before": events_before,
            "ws_state_after": st,
        },
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if pass_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
