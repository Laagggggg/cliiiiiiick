from __future__ import annotations

from pathlib import Path


ALLOWED_ARTIFACTS = {"equity_curve.png", "drawdown.png", "trade_markers.png"}


def artifact_target(request_path: str) -> Path | None:
    requested = Path(request_path).name
    if requested not in ALLOWED_ARTIFACTS:
        return None
    target = Path("artifacts") / requested
    return target if target.exists() and target.is_file() else None
