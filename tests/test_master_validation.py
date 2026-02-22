from omega_quant.live_gates import RISK_ACK_TEXT
from omega_quant.ops.master_validation import master_validation


def test_master_validation_release_ready_false_when_drift_bad(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "true")
    metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    out = master_validation(
        metrics,
        expected_features=[1, 2, 3, 4],
        actual_features=[10, 11, 12, 13],
        confirm_live=True,
        risk_ack=RISK_ACK_TEXT,
        paper_days=45,
        micro_live_days=45,
    )
    assert out["drift"]["gate"] == "FAIL"
    assert not out["release_ready"]


def test_master_validation_release_ready_true(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "true")
    metrics = {
        "wfe": 0.62,
        "dsr_confidence": 0.97,
        "pbo": 0.30,
        "white_rc_p": 0.03,
        "spa_p": 0.02,
        "recovery_factor": 3.4,
        "expectancy": 0.12,
    }
    out = master_validation(
        metrics,
        expected_features=[1, 2, 3, 4],
        actual_features=[1.0, 2.0, 3.0, 4.0],
        confirm_live=True,
        risk_ack=RISK_ACK_TEXT,
        paper_days=45,
        micro_live_days=45,
    )
    assert out["release_ready"]
    assert out["live"]["live_allowed"]
