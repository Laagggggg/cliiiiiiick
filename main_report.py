from __future__ import annotations

from pathlib import Path

from omega_quant.research.checklist import render_go_no_go_markdown
from omega_quant.research.report import render_report


if __name__ == "__main__":
    metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    report = render_report(metrics)
    Path("RESEARCH_REPORT.md").write_text(report)

    checklist = render_go_no_go_markdown(metrics)
    Path("GO_NO_GO_CHECKLIST.md").write_text(checklist)

    print("Wrote RESEARCH_REPORT.md and GO_NO_GO_CHECKLIST.md")
