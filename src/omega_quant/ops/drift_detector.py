from __future__ import annotations


def population_stability_index(expected: list[float], actual: list[float], bins: int = 10) -> float:
    """PSI approximation using equal-width bins."""
    if not expected or not actual:
        return 1.0

    lo = min(min(expected), min(actual))
    hi = max(max(expected), max(actual))
    if hi <= lo:
        return 0.0

    edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]

    def hist(vals: list[float]) -> list[float]:
        out = [0] * bins
        for v in vals:
            j = bins - 1
            for i in range(bins):
                if edges[i] <= v < edges[i + 1]:
                    j = i
                    break
            out[j] += 1
        total = max(1, len(vals))
        return [max(1e-6, c / total) for c in out]

    e = hist(expected)
    a = hist(actual)
    psi = sum((ai - ei) * __import__('math').log(ai / ei) for ei, ai in zip(e, a))
    return float(psi)


def drift_gate(expected: list[float], actual: list[float], psi_threshold: float = 0.20) -> dict:
    psi = population_stability_index(expected, actual)
    return {"psi": psi, "gate": "PASS" if psi <= psi_threshold else "FAIL"}
