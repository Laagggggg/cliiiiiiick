from __future__ import annotations

import math

GT_SCORE_LABEL = "HEURISTIC (non-peer-reviewed)"


def gt_score(mean_return: float, z_stat: float, r2: float, downside_vol: float) -> float:
    """GT-Score proxy heuristic: μ × ln(|z|+1) × R² / downside_vol."""
    denom = max(1e-9, downside_vol)
    return float(mean_return * math.log(abs(z_stat) + 1.0) * max(0.0, r2) / denom)
