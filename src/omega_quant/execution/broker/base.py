from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Order:
    symbol: str
    side: str
    qty: int
    price: float


@dataclass
class Fill:
    symbol: str
    side: str
    qty: int
    price: float
