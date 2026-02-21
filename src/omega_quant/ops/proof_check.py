from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _verify_checksums(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["missing checksum file"]
    errors: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split("  ", 1)
        f = Path(rel)
        if not f.exists():
            errors.append(f"missing artifact: {rel}")
            continue
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        if actual != digest:
            errors.append(f"checksum mismatch: {rel}")
    return len(errors) == 0, errors


def verify_paper_result(
    result_path: str = "artifacts/paper_cycle_result.json",
    ledger_path: str = "artifacts/paper_ledger.json",
    checksum_path: str = "artifacts/checksums.sha256",
    tol: float = 1e-6,
) -> dict:
    result_file = Path(result_path)
    ledger_file = Path(ledger_path)
    if not result_file.exists() or not ledger_file.exists():
        return {"ok": False, "reason": "missing_file", "paths": [str(result_file), str(ledger_file)]}

    result = json.loads(result_file.read_text(encoding="utf-8"))
    trades = json.loads(ledger_file.read_text(encoding="utf-8"))

    session_start = float(result.get("starting_capital", 0.0))
    session_end = float(result.get("ending_capital", 0.0))
    session_trade_count = int(result.get("session_trade_count", 0))

    if len(trades) < session_trade_count:
        return {"ok": False, "reason": "ledger_shorter_than_session", "ledger_count": len(trades), "session_count": session_trade_count}

    session_trades = trades[-session_trade_count:] if session_trade_count else []
    pnl_sum = sum(float(t.get("pnl_dollars", 0.0)) for t in session_trades)
    recomputed_end = session_start + pnl_sum
    delta = abs(recomputed_end - session_end)

    per_trade_ok = True
    for t in trades:
        before = float(t.get("equity_before", 0.0))
        after = float(t.get("equity_after", 0.0))
        pnl = float(t.get("pnl_dollars", 0.0))
        if abs((before + pnl) - after) > tol:
            per_trade_ok = False
            break

    checksums_ok, checksum_errors = _verify_checksums(Path(checksum_path))
    ok = delta <= tol and per_trade_ok and checksums_ok

    return {
        "ok": ok,
        "session_start": session_start,
        "session_end": session_end,
        "recomputed_end": recomputed_end,
        "delta": delta,
        "trade_consistency": per_trade_ok,
        "checksum_ok": checksums_ok,
        "checksum_errors": checksum_errors,
        "session_trade_count": session_trade_count,
        "ledger_trade_count": len(trades),
    }
