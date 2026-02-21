from __future__ import annotations

import os
import shutil


def system_health(min_free_gb: float = 1.0, max_load_per_cpu: float = 1.5) -> dict:
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024 ** 3)
    cpu_count = max(1, os.cpu_count() or 1)

    try:
        load_1m = os.getloadavg()[0]
    except (AttributeError, OSError):
        load_1m = 0.0

    normalized_load = load_1m / cpu_count
    checks = {
        "disk_ok": free_gb >= min_free_gb,
        "load_ok": normalized_load <= max_load_per_cpu,
    }
    return {
        "checks": checks,
        "free_gb": free_gb,
        "load_1m": load_1m,
        "normalized_load": normalized_load,
        "passed": all(checks.values()),
    }
