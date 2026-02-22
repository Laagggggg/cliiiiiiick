from omega_quant.engine import run_step


def mk_rows(vals):
    return [{"timestamp": f"t{i}", "open": v, "high": v + 1, "low": v - 1, "close": v, "volume": 100000} for i, v in enumerate(vals)]


def test_no_lookahead_score_not_affected_by_current_bar_close():
    base = [100 + i * 0.1 for i in range(80)]
    a = run_step(mk_rows(base + [110]), mk_rows([100 + i for i in range(40)]), equity=5000)
    b = run_step(mk_rows(base + [9999]), mk_rows([100 + i for i in range(40)]), equity=5000)
    assert a["score"] == b["score"]
    assert a["threshold"] == b["threshold"]


def test_engine_returns_enter_or_no_trade():
    out = run_step(mk_rows([100 + i * 0.2 for i in range(100)]), mk_rows([100 + i for i in range(50)]), equity=5000)
    assert out["status"] in {"ENTER", "NO_TRADE", "HALT"}
