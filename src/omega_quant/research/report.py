from __future__ import annotations


def go_no_go_checklist(metrics: dict) -> dict:
    checks = {
        "wf_efficiency": metrics.get("wfe", 0.0) > 0.50,
        "dsr_confidence": metrics.get("dsr_confidence", 0.0) > 0.95,
        "cpcv_pbo": metrics.get("pbo", 1.0) < 0.50,
        "white_rc": metrics.get("white_rc_p", 1.0) < 0.05,
        "spa": metrics.get("spa_p", 1.0) < 0.05,
        "recovery_factor": metrics.get("recovery_factor", 0.0) > 3.0,
        "expectancy": metrics.get("expectancy", -1.0) > 0,
    }
    return {
        "checks": checks,
        "go": all(checks.values()),
        "failed": [k for k, v in checks.items() if not v],
    }


def render_report(metrics: dict) -> str:
    result = go_no_go_checklist(metrics)
    lines = ["# RESEARCH REPORT", "", "## Metrics"]
    for k in sorted(metrics.keys()):
        lines.append(f"- {k}: {metrics[k]}")
    lines.extend(["", "## Go/No-Go", f"- Decision: {'GO' if result['go'] else 'NO-GO'}"])
    for name, passed in result["checks"].items():
        lines.append(f"- [{ 'x' if passed else ' '}] {name}")
    if result["failed"]:
        lines.append("- Failed checks: " + ", ".join(result["failed"]))
    return "\n".join(lines) + "\n"
