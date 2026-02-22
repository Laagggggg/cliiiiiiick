from __future__ import annotations

from dataclasses import dataclass

from omega_quant.types import Regime


@dataclass
class RegimeStateMachine:
    current: Regime = Regime.RANGING
    _trend_votes: int = 0
    _range_votes: int = 0
    _cooldown: int = 0

    def step(self, vote: Regime) -> Regime:
        if vote == Regime.AVOID:
            self.current = Regime.AVOID
            self._cooldown = 12
            self._trend_votes = 0
            self._range_votes = 0
            return self.current

        if self._cooldown > 0:
            self._cooldown -= 1
            return self.current

        if vote == Regime.TRENDING:
            self._trend_votes += 1
            self._range_votes = 0
        elif vote == Regime.RANGING:
            self._range_votes += 1
            self._trend_votes = 0

        if self.current != Regime.TRENDING and self._trend_votes >= 3:
            self.current = Regime.TRENDING
            self._trend_votes = 0
        elif self.current != Regime.RANGING and self._range_votes >= 3:
            self.current = Regime.RANGING
            self._range_votes = 0

        return self.current
