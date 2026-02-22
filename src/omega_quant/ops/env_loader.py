from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_if_present(path: str = ".env") -> bool:
    p = Path(path)
    if not p.exists():
        return False
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
    return True
