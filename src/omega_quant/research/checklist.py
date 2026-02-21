from __future__ import annotations

from omega_quant.research.report import go_no_go_checklist


def render_go_no_go_markdown(metrics: dict) -> str:
    result = go_no_go_checklist(metrics)
    lines = ["# GO / NO-GO CHECKLIST v5.0", "", "## AUTO-EVALUATED CHECKS"]
    for name, passed in result["checks"].items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")

    lines.extend([
        "",
        "## DECISION",
        f"- Decision: {'GO' if result['go'] else 'NO-GO'}",
    ])
    if result["failed"]:
        lines.append("- Failed checks: " + ", ".join(result["failed"]))
    return "\n".join(lines) + "\n"
