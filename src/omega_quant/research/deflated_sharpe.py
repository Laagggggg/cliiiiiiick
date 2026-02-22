from __future__ import annotations

import math


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def deflated_sharpe_ratio(observed_sharpe: float, sharpe_std: float, trials: int) -> dict:
    """
    Deflated Sharpe Ratio per Bailey & Lopez de Prado (2014).

    SR* = expected maximum Sharpe under null (all strategies random):
        SR* ≈ sqrt(2 * log(N)) * sigma   (Euler-Mascheroni corrected)

    z = (SR_observed - SR*) / sigma
    confidence = Phi(z)

    A confidence > 0.95 means the observed Sharpe likely exceeds what
    you'd expect from the best of N random strategies.
    """
    trials = max(1, int(trials))
    sigma = max(1e-9, float(sharpe_std))
    # Bailey & Lopez de Prado (2014) eq. — no arbitrary scaling
    sr_star = math.sqrt(max(0.0, 2.0 * math.log(trials))) * sigma
    z = (observed_sharpe - sr_star) / sigma
    confidence = _normal_cdf(z)
    return {
        "z": z,
        "confidence": confidence,
        "sr_star": sr_star,
        "gate": "PASS" if confidence > 0.95 else "FAIL",
    }
