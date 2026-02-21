from __future__ import annotations

from omega_quant.ops.master_validation import master_validation


def run_validation() -> dict:
    metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    expected = [1, 2, 3, 4, 5]
    actual = [1.1, 2.1, 3.0, 3.9, 5.2]
    return master_validation(metrics, expected, actual)


if __name__ == "__main__":
    print(run_validation())
