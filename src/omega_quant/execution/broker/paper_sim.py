from __future__ import annotations

from omega_quant.execution.broker.base import Fill, Order


class PaperBroker:
    def __init__(self, cash: float = 2000.0) -> None:
        self.cash = cash
        self.positions: dict[str, int] = {}

    def place_limit_order(self, order: Order, market_price: float) -> Fill | None:
        # naive fill rule: buy fills if limit >= market, sell fills if limit <= market
        if order.qty <= 0:
            return None
        if order.side == "BUY" and order.price >= market_price:
            cost = market_price * order.qty
            if cost > self.cash:
                return None
            self.cash -= cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.qty
            return Fill(order.symbol, order.side, order.qty, market_price)

        if order.side == "SELL" and order.price <= market_price:
            held = self.positions.get(order.symbol, 0)
            qty = min(order.qty, held)
            if qty <= 0:
                return None
            self.positions[order.symbol] = held - qty
            self.cash += market_price * qty
            return Fill(order.symbol, order.side, qty, market_price)

        return None
