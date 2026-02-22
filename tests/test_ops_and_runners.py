from omega_quant.ops.alerts import build_alert, should_alert_drift
from omega_quant.ops.logger import log_event


def test_logger_shape():
    e = log_event("info", "hello", a=1)
    assert e["level"] == "INFO"
    assert e["message"] == "hello"
    assert e["fields"]["a"] == 1


def test_alert_helpers():
    a = build_alert("log", "drift", "psi high", severity="warn")
    assert a["severity"] == "WARN"
    assert should_alert_drift(0.3)
    assert not should_alert_drift(0.1)
