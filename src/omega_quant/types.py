from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Regime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    AVOID = "AVOID"
    NEUTRAL = "NEUTRAL"


@dataclass
class CompositeSignal:
    score: float
    direction: str
    reason: str = ""


@dataclass
class Position:
    symbol: str
    shares: int
    current_price: float
    stop_price: float


@dataclass
class Trade:
    pnl: float
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0
    attribution: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class GuardResult:
    passed: bool
    failed_guard: str | None = None
    checks: Dict[str, bool] = field(default_factory=dict)


@dataclass
class WFSegment:
    is_sharpe: float
    oos_sharpe: float


@dataclass
class State:
    checks: Dict[str, bool]
    consecutive_losses: int = 0
    expectancy: float = 0.0
    portfolio_heat: float = 0.0
