from __future__ import annotations

from statistics import mean, pstdev

from omega_quant.types import Trade


class SignalAttributionTracker:
    def __init__(self) -> None:
        self._trades: list[Trade] = []

    def attribute_trade(self, trade: Trade, signals_at_entry: list[dict]) -> dict:
        total = sum(abs(s["score"] * s["weight"]) for s in signals_at_entry)
        attribution = {}
        for s in signals_at_entry:
            contribution = abs(s["score"] * s["weight"]) / total if total > 0 else 0.0
            attribution[s["family"]] = {
                "contribution_pct": contribution,
                "signal_score": s["score"],
                "weight_used": s["weight"],
                "pnl_attributed": trade.pnl * contribution,
            }
        trade.attribution = attribution
        self._trades.append(trade)
        return attribution

    def rolling_family_sharpe(self, family: str, window: int = 60) -> float:
        recent = self._trades[-window:]
        pnls = [t.attribution.get(family, {}).get("pnl_attributed", 0.0) for t in recent]
        if not pnls:
            return 0.0
        sd = pstdev(pnls) if len(pnls) > 1 else 0.0
        return mean(pnls) / (sd + 1e-8)
