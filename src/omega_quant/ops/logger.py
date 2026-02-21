from __future__ import annotations

from datetime import datetime, timezone


def log_event(level: str, message: str, **fields) -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "message": message,
        "fields": fields,
    }
