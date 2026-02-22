from omega_quant.execution.broker import Order, PaperBroker
from omega_quant.execution.cost_model import round_trip_cost_bps, stress_cost_bps
from omega_quant.research.report import go_no_go_checklist, render_report


def test_cost_model():
    c = round_trip_cost_bps(2, 1, 3, 0.5)
    assert c == 13.0
    assert stress_cost_bps(c, 6) == 78.0


def test_paper_broker_buy_sell_flow():
    broker = PaperBroker(cash=1000)
    buy = broker.place_limit_order(Order("SPY", "BUY", 5, 101), market_price=100)
    assert buy is not None
    assert broker.positions["SPY"] == 5
    sell = broker.place_limit_order(Order("SPY", "SELL", 3, 99), market_price=100)
    assert sell is not None
    assert broker.positions["SPY"] == 2


def test_reporting_go_no_go():
    metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    chk = go_no_go_checklist(metrics)
    assert chk["go"]
    txt = render_report(metrics)
    assert "Decision: GO" in txt
