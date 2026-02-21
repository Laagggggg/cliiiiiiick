from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _verify_checksums(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["missing checksum file"]
    errors: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
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
    tol_dollars: float = 0.01,
) -> dict:
    result_file = Path(result_path)
    ledger_file = Path(ledger_path)
    exists = result_file.exists() and ledger_file.exists()
    if not exists:
        return {"ok": False, "exists": False, "reason": "missing_file"}

    result = json.loads(result_file.read_text(encoding="utf-8"))
    trades = json.loads(ledger_file.read_text(encoding="utf-8"))
    session_count = int(result.get("session_trade_count", 0))
    session_trades = trades[-session_count:] if session_count else []
    start = float(result.get("starting_capital", 0.0))
    end = float(result.get("ending_capital", 0.0))

    pnl = sum(float(t.get("pnl_dollars", 0.0)) for t in session_trades)
    recomputed = start + pnl
    delta = abs(recomputed - end)

    per_trade_ok = all(isinstance(t.get("entry"), (int, float)) and isinstance(t.get("exit"), (int, float)) for t in trades)
    checks_ok, checksum_errors = _verify_checksums(Path(checksum_path))

    replay_hash = hashlib.sha256(json.dumps(session_trades, sort_keys=True).encode("utf-8")).hexdigest()
    recorded_hash = hashlib.sha256(json.dumps(result.get("session_trades", []), sort_keys=True).encode("utf-8")).hexdigest()
    replay_ok = replay_hash == recorded_hash

    ok = delta <= tol_dollars and per_trade_ok and checks_ok and replay_ok
    return {
        "ok": ok,
        "exists": True,
        "session_start": start,
        "session_end": end,
        "recomputed_end": recomputed,
        "delta": delta,
        "trade_consistency": per_trade_ok,
        "checksum_ok": checks_ok,
        "checksum_errors": checksum_errors,
        "replay_ok": replay_ok,
    }
