from __future__ import annotations

from omega_quant.execution.broker import Order, PaperBroker
from omega_quant.execution.cost_model import round_trip_cost_bps


if __name__ == "__main__":
    broker = PaperBroker(cash=2000)
    fill = broker.place_limit_order(Order("SPY", "BUY", 5, 101), market_price=100)
    cost = round_trip_cost_bps(2, 1, 1, 0.5)
    print({"fill": bool(fill), "cash": broker.cash, "rt_cost_bps": cost})
