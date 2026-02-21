from __future__ import annotations

import random

from omega_quant.research.backtest import run_simple_backtest
from omega_quant.strategy.hurst import hurst_exponent


def moving_avg(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
        else:
            out.append(sum(values[i - window + 1 : i + 1]) / window)
    return out


if __name__ == "__main__":
    random.seed(42)
    prices = [100.0]
    for _ in range(499):
        prices.append(prices[-1] * (1 + random.gauss(0.0002, 0.01)))

    ma_fast = moving_avg(prices, 20)
    ma_slow = moving_avg(prices, 50)

    entries, exits = [], []
    for i in range(len(prices)):
        f = ma_fast[i]
        s = ma_slow[i]
        fp = ma_fast[i - 1] if i > 0 else None
        sp = ma_slow[i - 1] if i > 0 else None
        entries.append(bool(f is not None and s is not None and fp is not None and sp is not None and f > s and fp <= sp))
        exits.append(bool(f is not None and s is not None and fp is not None and sp is not None and f < s and fp >= sp))

    report = run_simple_backtest(prices, entries, exits)
    h = hurst_exponent(prices)
    print({**report, "hurst": round(h, 3)})
