from __future__ import annotations

from omega_quant.data.reconciler import reconcile_prices
from omega_quant.data.validator import validate_ohlcv
from omega_quant.execution.broker import Order, PaperBroker
from omega_quant.risk.guards import REQUIRED_GUARDS, guard_all_v5
from omega_quant.risk.sizing import calculate_position_size_v5
from omega_quant.strategy.adaptive_threshold import adaptive_entry_threshold
from omega_quant.strategy.adaptive_weights import compute_adaptive_weights
from omega_quant.strategy.signals.composite import compute_composite_signal
from omega_quant.types import State


def run_pipeline_step(
    rows: list[dict],
    primary_prices: list[float],
    secondary_prices: list[float],
    trend_signal: float,
    reversion_signal: float,
    regime: str,
    regime_conf: float,
    hurst_value: float,
    htf_bias: str,
    broker: PaperBroker,
    *,
    guard_checks: dict[str, bool] | None = None,
    expectancy: float = 0.1,
    consecutive_losses: int = 0,
    portfolio_heat: float = 0.01,
) -> dict:
    data_check = validate_ohlcv(rows)
    if not data_check["passed"]:
        return {"status": "HALT", "reason": "data_validation_failed", "details": data_check}

    rec = reconcile_prices(primary_prices, secondary_prices, tolerance_pct=0.5)
    if not rec["passed"]:
        return {"status": "HALT", "reason": "reconciliation_failed", "details": rec}

    # Use real guard state; default to fail-closed (all False) if not provided
    if guard_checks is not None:
        checks = {k: guard_checks.get(k, False) for k in REQUIRED_GUARDS}
    else:
        checks = {k: False for k in REQUIRED_GUARDS}
    # Data guards are satisfied by the checks above
    checks["data_quality"] = data_check["passed"]
    checks["data_reconciliation"] = rec["passed"]
    guard = guard_all_v5(State(checks=checks, expectancy=expectancy, consecutive_losses=consecutive_losses, portfolio_heat=portfolio_heat))
    if not guard.passed:
        return {"status": "HALT", "reason": f"guard_failed:{guard.failed_guard}"}

    weights = compute_adaptive_weights(regime, {"trend": 1.0, "reversion": 0.5})
    signal, threshold = compute_composite_signal(
        regime=regime,
        regime_confidence=regime_conf,
        hurst_value=hurst_value,
        trend=trend_signal,
        reversion=reversion_signal,
        quality_gate=1.0,
        macro_overlay=1.0,
        fractal_conf=min(1.0, abs(hurst_value - 0.5) * 2),
        htf_bias=htf_bias,
        adaptive_weights=weights,
    )

    adaptive_thr = adaptive_entry_threshold(regime, regime_conf, hurst_value)
    if signal.score <= max(threshold, adaptive_thr):
        return {"status": "NO_TRADE", "score": signal.score, "threshold": max(threshold, adaptive_thr)}

    entry = primary_prices[-1]
    size = calculate_position_size_v5(
        capital=broker.cash,
        entry=entry,
        atr=max(0.01, entry * 0.01),
        signal_conf=min(1.0, signal.score),
        regime_conf=regime_conf,
        alignment=1.0,
        macro=1.0,
        hurst=hurst_value,
        cb_mult=1.0,
        portfolio_heat_remaining=max(1.0, broker.cash * 0.06),
    )
    if size <= 0:
        return {"status": "NO_TRADE", "reason": "size_zero"}

    fill = broker.place_limit_order(Order("SPY", "BUY", size, entry), market_price=entry)
    return {
        "status": "TRADE" if fill else "NO_FILL",
        "size": size,
        "fill": bool(fill),
        "score": signal.score,
        "threshold": max(threshold, adaptive_thr),
    }
