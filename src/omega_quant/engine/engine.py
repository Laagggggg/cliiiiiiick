from __future__ import annotations


def run_step(closes: list[float], equity: float) -> dict:
    """Canonical strategy step used by paper/backtest/monitor code paths.

    The engine computes a decision from historical closes only and, when trading,
    uses real bar closes for both entry and exit prices:
      - entry: previous bar close
      - exit: latest bar close
    """
    if len(closes) < 22:
        return {
            "status": "NO_TRADE",
            "reason": "insufficient_bars",
            "score": 0.0,
            "threshold": 0.02,
            "regime": "UNKNOWN",
        }

    sma5 = sum(closes[-6:-1]) / 5.0
    sma20 = sum(closes[-21:-1]) / 20.0
    trend_signal = (closes[-2] - closes[-6]) / closes[-6]
    score = max(0.0, trend_signal * 40.0)
    threshold = 0.02
    regime = "TREND" if sma5 > sma20 else "MEAN_REVERT"

    should_trade = score > threshold and closes[-2] > sma20
    if not should_trade:
        return {
            "status": "NO_TRADE",
            "reason": "score_or_bias_below_threshold",
            "score": score,
            "threshold": threshold,
            "regime": regime,
        }

    entry = closes[-2]
    exit_ = closes[-1]
    qty = round((equity * 0.15) / entry, 6) if entry > 0 else 0.0
    if qty <= 0:
        return {
            "status": "NO_TRADE",
            "reason": "size_zero",
            "score": score,
            "threshold": threshold,
            "regime": regime,
        }

    pnl = (exit_ - entry) * qty
    return {
        "status": "TRADE_FILLED",
        "reason": "trend_above_threshold",
        "score": score,
        "threshold": threshold,
        "regime": regime,
        "entry": entry,
        "exit": exit_,
        "qty": qty,
        "pnl": pnl,
    }
