from __future__ import annotations

import json
from pathlib import Path


def verify_paper_result(path: str = "artifacts/paper_cycle_result.json", tol: float = 1e-6) -> dict:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "missing_file", "path": str(p)}

    data = json.loads(p.read_text(encoding="utf-8"))
    start = float(data.get("starting_capital", 0.0))
    end = float(data.get("ending_capital", 0.0))
    trades = data.get("trades", [])

    pnl_sum = sum(float(t.get("pnl_dollars", 0.0)) for t in trades)
    recomputed_end = start + pnl_sum
    delta = abs(recomputed_end - end)

    monotonic_checks = []
    for t in trades:
        before = float(t.get("equity_before", 0.0))
        after = float(t.get("equity_after", 0.0))
        growth = float(t.get("equity_growth_dollars", 0.0))
        monotonic_checks.append(abs((before + growth) - after) <= tol)

    ok = delta <= tol and all(monotonic_checks)
    return {
        "ok": ok,
        "path": str(p),
        "start": start,
        "end": end,
        "recomputed_end": recomputed_end,
        "delta": delta,
        "trade_consistency": all(monotonic_checks),
        "trade_count": len(trades),
    }
