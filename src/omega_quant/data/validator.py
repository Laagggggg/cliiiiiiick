from __future__ import annotations


def validate_ohlcv(rows: list[dict]) -> dict:
    checks = {"no_nans": True, "high_ge_low": True, "close_in_range": True, "positive_volume": True}
    for r in rows:
        try:
            o = float(r["open"])
            h = float(r["high"])
            l = float(r["low"])
            c = float(r["close"])
            v = float(r["volume"])
        except Exception:
            checks["no_nans"] = False
            continue
        if h < l:
            checks["high_ge_low"] = False
        if c > h or c < l:
            checks["close_in_range"] = False
        if v < 0:
            checks["positive_volume"] = False
        _ = o
    return {"passed": all(checks.values()), "checks": checks}
