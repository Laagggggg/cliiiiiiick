from omega_quant.strategy.adaptive_threshold import adaptive_entry_threshold
from omega_quant.strategy.adaptive_weights import compute_adaptive_weights
from omega_quant.strategy.hurst import hurst_regime
from omega_quant.strategy.regime import classify_regime
from omega_quant.strategy.signals.composite import compute_composite_signal
from omega_quant.types import Regime


def test_regime_weighting_and_hurst_cap():
    votes = {
        "adx": Regime.TRENDING,
        "vol": Regime.TRENDING,
        "ma": Regime.TRENDING,
        "hmm": Regime.TRENDING,
        "hurst": Regime.TRENDING,
        "autocorr": Regime.TRENDING,
    }
    regime, conf = classify_regime(votes, hurst_value=0.50)
    assert regime == Regime.TRENDING
    assert conf <= 0.5


def test_adaptive_weights_and_threshold():
    w = compute_adaptive_weights("TRENDING", {"trend": 1.2, "reversion": 0.2})
    assert abs(sum(w.values()) - 1.0) < 1e-9
    thr = adaptive_entry_threshold("TRENDING", 0.8, 0.6)
    assert 0.35 <= thr <= 0.65


def test_composite_signal_long_when_strong():
    signal, threshold = compute_composite_signal(
        regime="TRENDING",
        regime_confidence=0.8,
        hurst_value=0.65,
        trend=0.9,
        reversion=0.1,
        quality_gate=1.0,
        macro_overlay=1.0,
        fractal_conf=0.8,
        htf_bias="BULLISH",
        adaptive_weights={"trend": 0.9, "reversion": 0.1},
    )
    assert signal.score > threshold
    assert signal.direction == "LONG"


def test_hurst_regime_boundaries():
    assert hurst_regime(0.7) == Regime.TRENDING
    assert hurst_regime(0.3) == Regime.RANGING
    assert hurst_regime(0.5) == Regime.NEUTRAL
