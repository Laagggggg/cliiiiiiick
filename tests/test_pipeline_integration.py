from omega_quant.execution.broker import PaperBroker
from omega_quant.ops.pipeline import run_pipeline_step
from omega_quant.risk.guards import REQUIRED_GUARDS


def _rows():
    return [
        {"timestamp": "2026-01-01T10:00:00Z", "open": "100", "high": "101", "low": "99", "close": "100", "volume": "1000"},
        {"timestamp": "2026-01-01T11:00:00Z", "open": "100", "high": "102", "low": "99", "close": "101", "volume": "1200"},
    ]


def test_pipeline_trade_path():
    broker = PaperBroker(cash=5000)
    all_guards = {k: True for k in REQUIRED_GUARDS}
    out = run_pipeline_step(
        rows=_rows(),
        primary_prices=[100, 101],
        secondary_prices=[100.1, 101.1],
        trend_signal=0.95,
        reversion_signal=0.1,
        regime="TRENDING",
        regime_conf=0.8,
        hurst_value=0.65,
        htf_bias="BULLISH",
        broker=broker,
        guard_checks=all_guards,
    )
    assert out["status"] in {"TRADE", "NO_FILL", "NO_TRADE"}


def test_pipeline_halts_on_bad_data():
    broker = PaperBroker(cash=5000)
    bad = [{"timestamp": "t", "open": "x", "high": "1", "low": "2", "close": "3", "volume": "4"}]
    out = run_pipeline_step(
        rows=bad,
        primary_prices=[100],
        secondary_prices=[100],
        trend_signal=1.0,
        reversion_signal=0.0,
        regime="TRENDING",
        regime_conf=0.9,
        hurst_value=0.7,
        htf_bias="BULLISH",
        broker=broker,
    )
    assert out["status"] == "HALT"
