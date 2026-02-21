from omega_quant.engine import run_step


def mk_rows(closes: list[float]) -> list[dict]:
    return [{"timestamp": f"t{i}", "open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 1} for i, c in enumerate(closes)]


def test_engine_uses_real_bar_prices_for_fills():
    rows = mk_rows([100 + i * 0.5 for i in range(40)])
    out = run_step(rows, equity=5000)
    assert out["status"] == "TRADE_FILLED"
    assert out["entry"] == rows[-2]["close"]
    assert out["exit"] == rows[-1]["close"]


def test_engine_no_trade_when_insufficient_data():
    out = run_step(mk_rows([100, 101, 102]), equity=5000)
    assert out["status"] == "NO_TRADE"


def test_no_lookahead_future_spike_does_not_change_score():
    base = [100 + i * 0.1 for i in range(30)]
    a = mk_rows(base + [110])
    b = mk_rows(base + [9999])
    out_a = run_step(a, equity=5000)
    out_b = run_step(b, equity=5000)
    assert out_a["score"] == out_b["score"]
    assert out_a["threshold"] == out_b["threshold"]
