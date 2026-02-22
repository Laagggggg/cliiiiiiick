from __future__ import annotations

from statistics import mean

from omega_quant.types import WFSegment


def walk_forward_efficiency(segments: list[WFSegment], min_wfe: float = 0.5, min_pass_rate: float = 0.7) -> dict:
    if not segments:
        return {"wfe": 0.0, "pass_rate": 0.0, "gate": "FAIL"}
    is_sharpes = [s.is_sharpe for s in segments]
    oos_sharpes = [s.oos_sharpe for s in segments]
    mean_is = mean(is_sharpes)
    wfe = (mean(oos_sharpes) / mean_is) if mean_is > 0 else 0.0
    pass_rate = sum(1 for s in oos_sharpes if s > 0) / len(oos_sharpes)
    gate = "PASS" if wfe > min_wfe and pass_rate > min_pass_rate else "FAIL"
    return {"wfe": wfe, "pass_rate": pass_rate, "gate": gate}
