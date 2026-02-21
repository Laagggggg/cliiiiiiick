from __future__ import annotations

import csv


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if not rows:
        raise ValueError("empty csv")
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    return rows
