from __future__ import annotations


def run_step(rows: list[dict], equity: float) -> dict:
    if len(rows) < 25:
        return {"status": "NO_TRADE", "reason": "insufficient_bars", "score": 0.0, "threshold": 0.25, "regime": "UNKNOWN"}

    closes = [float(r["close"]) for r in rows]
    # no-lookahead: decision uses rows up to i-1; execution uses i
    decision_slice = closes[:-1]
    exec_bar_close = closes[-1]

    sma_fast = sum(decision_slice[-5:]) / 5.0
    sma_slow = sum(decision_slice[-20:]) / 20.0
    momentum = (decision_slice[-1] - decision_slice[-5]) / decision_slice[-5]
    volatility = max(1e-9, (max(decision_slice[-10:]) - min(decision_slice[-10:])) / decision_slice[-10])

    score = max(0.0, momentum * 30.0)
    threshold = 0.20 + min(0.20, volatility * 10.0)
    regime = "TREND" if sma_fast > sma_slow else "MEAN_REVERT"

    if score <= threshold:
        return {
            "status": "NO_TRADE",
            "reason": f"Score {score:.3f} < threshold {threshold:.3f}",
            "score": score,
            "threshold": threshold,
            "regime": regime,
        }

    entry = decision_slice[-1]
    exit_ = exec_bar_close
    qty = round((equity * 0.10) / entry, 6) if entry > 0 else 0.0
    if qty <= 0:
        return {"status": "NO_TRADE", "reason": "size_zero", "score": score, "threshold": threshold, "regime": regime}

    return {
        "status": "TRADE_FILLED",
        "reason": f"Score {score:.3f} >= threshold {threshold:.3f} in {regime}",
        "score": score,
        "threshold": threshold,
        "regime": regime,
        "entry": entry,
        "exit": exit_,
        "qty": qty,
        "pnl": (exit_ - entry) * qty,
    }
