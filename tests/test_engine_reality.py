from omega_quant.engine import run_step


def test_engine_uses_real_bar_prices_for_fills():
    closes = [100 + i * 0.2 for i in range(30)]
    out = run_step(closes, equity=5000)
    assert out["status"] == "TRADE_FILLED"
    assert out["entry"] == closes[-2]
    assert out["exit"] == closes[-1]


def test_engine_no_trade_when_insufficient_data():
    out = run_step([100, 101, 102], equity=5000)
    assert out["status"] == "NO_TRADE"
    assert out["reason"] == "insufficient_bars"
