from __future__ import annotations


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def hurst_multiplier(hurst: float) -> float:
    mult = 1.0 + (abs(hurst - 0.5) - 0.10) * 0.5
    return _clamp(mult, 0.70, 1.15)


def calculate_position_size_v5(
    capital: float,
    entry: float,
    atr: float,
    signal_conf: float,
    regime_conf: float,
    alignment: float,
    macro: float,
    hurst: float,
    cb_mult: float,
    portfolio_heat_remaining: float,
    max_position_pct: float = 0.20,
    per_trade_risk_pct: float = 0.01,
    kelly_fraction: float = 0.25,
    win_rate: float = 0.50,
    avg_win_loss_ratio: float = 1.20,
) -> int:
    if capital <= 0 or entry <= 0 or atr <= 0:
        return 0

    # Kelly (safe fallback around edge cases)
    if avg_win_loss_ratio <= 0:
        kelly_pct = 0.0
    else:
        kelly_pct = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
    kelly_pct = max(0.0, kelly_pct)

    kelly_size = capital * kelly_pct * kelly_fraction / entry
    fixed_frac_size = (capital * per_trade_risk_pct) / (atr * 2)
    # Use Kelly when it yields a positive size; fall back to fixed fraction otherwise.
    # Cap at fixed fraction to prevent over-leverage from aggressive Kelly estimates.
    if kelly_size > 0:
        base = min(kelly_size, fixed_frac_size * 2.0)  # allow Kelly up to 2x fixed frac
    else:
        base = fixed_frac_size

    h_mult = hurst_multiplier(hurst)
    composite = signal_conf * regime_conf * alignment * macro * h_mult * cb_mult
    raw = int(base * composite)

    # heat remaining is in dollars-at-risk, stop distance = 2*ATR
    stop_dist = atr * 2
    max_by_heat = int(portfolio_heat_remaining / stop_dist) if stop_dist > 0 else 0
    raw = min(raw, max_by_heat)

    # position cap
    pos_cap = int((capital * max_position_pct) / entry)
    final = min(raw, pos_cap)

    if final * entry < 100:
        return 0
    return max(0, final)
