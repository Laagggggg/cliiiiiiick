from __future__ import annotations

import math


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def deflated_sharpe_ratio(observed_sharpe: float, sharpe_std: float, trials: int) -> dict:
    """
    Lightweight DSR proxy:
    z = (SR - SR*) / sigma, with SR* approximated as sqrt(2 log(trials)).
    Returns p-value-like confidence in [0,1].
    """
    trials = max(1, int(trials))
    sigma = max(1e-9, float(sharpe_std))
    sr_star = math.sqrt(max(0.0, 2.0 * math.log(trials))) / 10.0
    z = (observed_sharpe - sr_star) / sigma
    confidence = _normal_cdf(z)
    return {
        "z": z,
        "confidence": confidence,
        "gate": "PASS" if confidence > 0.95 else "FAIL",
    }
