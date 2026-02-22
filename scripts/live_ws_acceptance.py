from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

from omega_quant.monitor.live_ws import ensure_websocket, get_ws_state


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=int, default=30)
    args = p.parse_args()

    out = Path("artifacts/live_ws_acceptance.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    keys_present = bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_API_SECRET"))
    ws_lib = importlib.util.find_spec("websockets") is not None
    if not keys_present or not ws_lib:
        result = {
            "status": "SKIP",
            "reason": "requires_keys_or_websockets",
            "next_action": "Set .env Alpaca keys and install websockets, then rerun.",
            "metrics": {"keys_present": keys_present, "websockets_installed": ws_lib},
        }
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0

    ensure_websocket("SPY")
    start = time.time()
    event_count = 0
    last = {}
    while time.time() - start < args.seconds:
        st = get_ws_state()
        last = st
        event_count = int(bool(st.get("last_quote_ts"))) + int(bool(st.get("last_trade_ts"))) + int(bool(st.get("last_bar_ts")))
        if event_count > 0:
            break
        time.sleep(1)

    ok = event_count > 0
    result = {
        "status": "PASS" if ok else "FAIL",
        "reason": "" if ok else "ws_connected_no_qtb_events",
        "next_action": "Check Alpaca data entitlements/subscription and websocket auth" if not ok else "None",
        "metrics": {
            "event_count": event_count,
            "transport": last.get("transport"),
            "last_quote_ts": last.get("last_quote_ts"),
            "last_trade_ts": last.get("last_trade_ts"),
            "last_bar_ts": last.get("last_bar_ts"),
            "connected": last.get("connected"),
        },
    }
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
