from __future__ import annotations

import math


def _hurst_like(prices: list[float]) -> float:
    if len(prices) < 20:
        return 0.5
    diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    m = sum(diffs) / len(diffs)
    var = sum((d - m) ** 2 for d in diffs) / max(1, len(diffs) - 1)
    rs = (max(prices) - min(prices)) / (math.sqrt(var) + 1e-9)
    return max(0.0, min(1.0, math.log(rs + 1.0) / math.log(len(prices) + 1.0)))


def _autocorr(vals: list[float], lag: int) -> float:
    if len(vals) <= lag + 2:
        return 0.0
    x = vals[:-lag]
    y = vals[lag:]
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = sum((a - mx) ** 2 for a in x)
    deny = sum((b - my) ** 2 for b in y)
    return num / (math.sqrt(denx * deny) + 1e-9)


def run_step(rows_1h: list[dict], rows_1d: list[dict] | None, equity: float, has_position: bool = False, entry_price: float | None = None, hold_bars: int = 0) -> dict:
    if len(rows_1h) < 40:
        return {"status": "HALT", "reason": "stale_or_short_data", "score": 0.0, "threshold": 1.0, "regime": "AVOID", "guards": {"stale_data": False}}

    closes = [float(r["close"]) for r in rows_1h]
    if any(math.isnan(c) or math.isinf(c) for c in closes):
        return {"status": "HALT", "reason": "nan_inf_data", "score": 0.0, "threshold": 1.0, "regime": "AVOID", "guards": {"nan": False}}

    decision = closes[:-1]  # no-lookahead
    exec_price = closes[-1]

    fast = sum(decision[-8:]) / 8
    slow = sum(decision[-21:]) / 21
    adx_proxy = abs(fast - slow) / slow
    vol_ratio = (max(decision[-20:]) - min(decision[-20:])) / decision[-20]
    hurst = _hurst_like(decision[-30:])
    ac1 = _autocorr(decision[-30:], 1)
    ac5 = _autocorr(decision[-30:], 5)

    htf_bias = 0.0
    if rows_1d and len(rows_1d) >= 20:
        d = [float(r["close"]) for r in rows_1d[:-1]]
        htf_bias = 1.0 if d[-1] > (sum(d[-20:]) / 20) else -1.0

    regime_votes = 0
    regime_votes += 1 if adx_proxy > 0.001 else -1
    regime_votes += 1 if hurst > 0.55 else -1
    regime_votes += 1 if (ac1 + ac5) > 0 else -1
    regime = "TREND" if regime_votes >= 2 else ("RANGE" if regime_votes <= -2 else "AVOID")

    trend = max(0.0, (decision[-1] - decision[-5]) / decision[-5])
    reversion = max(0.0, (sum(decision[-5:]) / 5 - decision[-1]) / decision[-1])
    quality = max(0.0, 1.0 - min(0.8, vol_ratio * 10))
    score = trend * 0.55 + reversion * 0.15 + quality * 0.20 + (0.10 if htf_bias > 0 else 0.0)
    regime_conf = min(1.0, abs(regime_votes) / 3)
    threshold = 0.22 + (0.10 * (1 - regime_conf)) + abs(hurst - 0.5) * 0.05

    if regime == "AVOID":
        return {"status": "NO_TRADE", "reason": "Regime AVOID", "score": score, "threshold": threshold, "regime": regime, "hurst": hurst, "regime_confidence": regime_conf}

    # exit logic
    if has_position and entry_price is not None:
        stop = entry_price * 0.992
        take = entry_price * 1.008
        if exec_price <= stop:
            return {"status": "EXIT", "reason": "stop_loss", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price}
        if exec_price >= take:
            return {"status": "EXIT", "reason": "take_profit", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price}
        if hold_bars >= 12:
            return {"status": "EXIT", "reason": "time_stop", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price}
        if score < threshold * 0.8:
            return {"status": "EXIT", "reason": "signal_exit", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price}
        return {"status": "HOLD", "reason": "hold", "score": score, "threshold": threshold, "regime": regime}

    if score < threshold:
        return {"status": "NO_TRADE", "reason": f"Score {score:.3f} < threshold {threshold:.3f}", "score": score, "threshold": threshold, "regime": regime}

    qty = round((equity * 0.08) / decision[-1], 6)
    return {
        "status": "ENTER",
        "reason": f"Score {score:.3f} >= threshold {threshold:.3f}",
        "score": score,
        "threshold": threshold,
        "regime": regime,
        "entry_signal_price": decision[-1],
        "qty": max(0.0, qty),
        "hurst": hurst,
        "regime_confidence": regime_conf,
    }
