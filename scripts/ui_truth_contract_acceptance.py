from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from omega_quant.ui_service import run_action


REQUIRED = ["mode_truth", "data_grade", "transport", "provider_primary", "provider_secondary", "recon_status", "freshness_seconds", "freshness_label", "last_bar_ts", "next_action", "decision_sentence"]


def assert_truth(payload: dict) -> None:
    for k in REQUIRED:
        if k not in payload:
            raise AssertionError(f"missing:{k}")
        if str(payload[k]).strip() == "":
            raise AssertionError(f"blank:{k}")


def main() -> int:
    out_path = Path("artifacts/ui_truth_contract_acceptance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sequence = [
        run_action("paper_account"),
        run_action("websocket_monitor"),
        run_action("reset_paper", {"starting_capital": 1000}),
        run_action("paper", {"starting_capital": 1000, "cycles": 1}),
        run_action("live_monitor"),
        run_action("paper_account"),
    ]
    try:
        for s in sequence:
            assert_truth(s)
        result = {"status": "PASS", "checks": len(sequence)}
        rc = 0
    except Exception as exc:  # noqa: BLE001
        result = {"status": "FAIL", "error": str(exc), "last": sequence[-1] if sequence else {}}
        rc = 1

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
