from omega_quant.research.checklist import render_go_no_go_markdown


def test_checklist_generation_go_and_nogo():
    go_metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    txt_go = render_go_no_go_markdown(go_metrics)
    assert "Decision: GO" in txt_go

    bad = dict(go_metrics)
    bad["wfe"] = 0.2
    txt_bad = render_go_no_go_markdown(bad)
    assert "Decision: NO-GO" in txt_bad
