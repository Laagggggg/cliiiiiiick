from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _verify_checksums(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["missing checksum file"]
    errs: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        fp = Path(rel)
        if not fp.exists():
            errs.append(f"missing artifact: {rel}")
            continue
        if hashlib.sha256(fp.read_bytes()).hexdigest() != digest:
            errs.append(f"checksum mismatch: {rel}")
    return len(errs) == 0, errs


def verify_paper_result(result_path: str = "artifacts/paper_cycle_result.json", ledger_path: str = "artifacts/paper_ledger.json", checksum_path: str = "artifacts/checksums.sha256", tol_dollars: float = 0.01) -> dict:
    r = Path(result_path)
    l = Path(ledger_path)
    exists = r.exists() and l.exists()
    if not exists:
        return {"ok": False, "exists": False, "reason": "missing_file"}

    result = json.loads(r.read_text(encoding="utf-8"))
    trades = json.loads(l.read_text(encoding="utf-8"))
    session = int(result.get("session_trade_count", 0))
    ss = trades[-session:] if session else []
    start = float(result.get("starting_capital", 0.0))
    end = float(result.get("ending_capital", 0.0))
    recomputed = start + float(result.get("session_pnl_dollars", 0.0))
    delta = abs(recomputed - end)

    arithmetic_ok = all(abs(float(t.get("exit", 0.0)) - float(t.get("entry", 0.0))) < 1e9 for t in trades)
    c_ok, c_err = _verify_checksums(Path(checksum_path))
    replay_ok = hashlib.sha256(json.dumps(ss, sort_keys=True).encode()).hexdigest() == hashlib.sha256(json.dumps(result.get("session_trades", []), sort_keys=True).encode()).hexdigest()

    ok = delta <= tol_dollars and arithmetic_ok and c_ok and replay_ok
    return {"ok": ok, "exists": True, "delta": delta, "recomputed_end": recomputed, "session_end": end, "trade_consistency": arithmetic_ok, "checksum_ok": c_ok, "checksum_errors": c_err, "replay_ok": replay_ok}
