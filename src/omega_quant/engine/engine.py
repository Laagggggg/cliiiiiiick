from __future__ import annotations

import math


def _hurst_like(prices: list[float]) -> float:
    """Lightweight Hurst proxy for the engine (fast path)."""
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


def _atr(rows: list[dict], period: int = 14) -> float:
    """Average True Range over the last `period` bars."""
    if len(rows) < period + 1:
        return 0.0
    trs: list[float] = []
    for i in range(-period, 0):
        h = float(rows[i]["high"])
        lo = float(rows[i]["low"])
        prev_c = float(rows[i - 1]["close"])
        tr = max(h - lo, abs(h - prev_c), abs(lo - prev_c))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else 0.0


def run_step(rows_1h: list[dict], rows_1d: list[dict] | None, equity: float, has_position: bool = False, entry_price: float | None = None, hold_bars: int = 0) -> dict:
    if len(rows_1h) < 40:
        return {"status": "HALT", "reason": "stale_or_short_data", "score": 0.0, "threshold": 1.0, "regime": "AVOID", "guards": {"stale_data": False}}

    closes = [float(r["close"]) for r in rows_1h]
    if any(math.isnan(c) or math.isinf(c) for c in closes):
        return {"status": "HALT", "reason": "nan_inf_data", "score": 0.0, "threshold": 1.0, "regime": "AVOID", "guards": {"nan": False}}

    decision = closes[:-1]  # no-lookahead
    exec_price = closes[-1]
    atr = _atr(rows_1h[:-1], period=14)  # ATR from decision bars only
    if atr <= 0:
        atr = abs(decision[-1]) * 0.005  # fallback: 0.5% of price

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

    # Exit logic — ATR-based stops for proper risk/reward
    if has_position and entry_price is not None:
        stop_mult = 2.0   # 2x ATR stop loss
        target_mult = 3.0  # 3x ATR take profit (1.5:1 R:R)
        stop = entry_price - atr * stop_mult
        take = entry_price + atr * target_mult

        if exec_price <= stop:
            return {"status": "EXIT", "reason": "stop_loss", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price, "atr": atr}
        if exec_price >= take:
            return {"status": "EXIT", "reason": "take_profit", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price, "atr": atr}
        if hold_bars >= 20:
            return {"status": "EXIT", "reason": "time_stop", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price, "atr": atr}
        if score < threshold * 0.7:
            return {"status": "EXIT", "reason": "signal_exit", "score": score, "threshold": threshold, "regime": regime, "exit": exec_price, "atr": atr}
        return {"status": "HOLD", "reason": "hold", "score": score, "threshold": threshold, "regime": regime, "atr": atr}

    if score < threshold:
        return {"status": "NO_TRADE", "reason": f"Score {score:.3f} < threshold {threshold:.3f}", "score": score, "threshold": threshold, "regime": regime}

    # Position sizing: 2% risk per trade based on ATR stop
    risk_per_trade = equity * 0.02
    stop_distance = atr * 2.0
    qty = round(risk_per_trade / stop_distance, 6) if stop_distance > 0 else 0.0
    # Cap at 20% of equity
    max_qty = (equity * 0.20) / decision[-1] if decision[-1] > 0 else 0.0
    qty = min(qty, max_qty)

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
        "atr": atr,
    }
