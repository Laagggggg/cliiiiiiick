from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_if_present(path: str | None = None, *, override: bool = True) -> bool:
    target = Path(path) if path else (Path.cwd() / ".env")
    if not target.exists():
        return False
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not k:
            continue
        if override or k not in os.environ:
            os.environ[k] = v
    return True
