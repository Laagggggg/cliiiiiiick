from __future__ import annotations

import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIMEZONE_NEXT_ACTION = "Install tzdata (python -m pip install tzdata) and rerun"


def market_timezone_status() -> dict:
    try:
        ZoneInfo("America/New_York")
        return {"ok": True, "status": "ok", "reason": "timezone_ready", "next_action": "None"}
    except ZoneInfoNotFoundError:
        return {
            "ok": False,
            "status": "HALT",
            "reason": "timezone_missing",
            "decision_sentence": "HALT: market timezone America/New_York unavailable. Next: install tzdata",
            "next_action": TIMEZONE_NEXT_ACTION,
        }


def _parse_ts(ts: str | None) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    clean = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_rth(timestamp: str | None = None) -> bool:
    tz = market_timezone_status()
    if not tz["ok"]:
        return False
    dt = _parse_ts(timestamp).astimezone(ZoneInfo("America/New_York"))
    if dt.weekday() >= 5:
        return False
    return time(9, 30) <= dt.time() <= time(16, 0)


def should_block_new_orders(timestamp: str | None = None, ext_hours: bool | None = None) -> bool:
    allow_ext = ext_hours if ext_hours is not None else os.getenv("EXT_HOURS", "false").lower() == "true"
    return not allow_ext and not is_rth(timestamp)
