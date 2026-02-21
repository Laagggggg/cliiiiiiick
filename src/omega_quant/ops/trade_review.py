from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_trade_review(path: str, review: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = {"timestamp_utc": _utc(), **review}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def render_trade_reviews_markdown(jsonl_path: str, markdown_path: str) -> None:
    src = Path(jsonl_path)
    dst = Path(markdown_path)
    rows = []
    if src.exists():
        for ln in src.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue

    lines = [
        "# Paper Trade Reviews",
        "",
        "| Time (UTC) | Status | Score | Threshold | Reason |",
        "|---|---:|---:|---:|---|",
    ]
    for r in rows[-200:]:
        lines.append(
            f"| {r.get('timestamp_utc','')} | {r.get('status','')} | {r.get('score','')} | {r.get('threshold','')} | {r.get('reason','')} |"
        )

    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
