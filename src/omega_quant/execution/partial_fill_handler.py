from __future__ import annotations


def handle_partial_fill(fill_qty: float, intended_qty: float, signal_strength: float, entry_threshold: float, min_partial_fill_pct: float = 0.5) -> tuple[str, float]:
    if intended_qty <= 0:
        return "CANCEL_REMAINDER", 0.0
    fill_pct = fill_qty / intended_qty
    if fill_pct >= min_partial_fill_pct:
        return "ACCEPT", fill_qty
    if signal_strength > entry_threshold + 0.15:
        return "REQUEUE", max(0.0, intended_qty - fill_qty)
    return "CANCEL_REMAINDER", fill_qty
