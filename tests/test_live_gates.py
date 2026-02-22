from omega_quant.live_gates import RISK_ACK_TEXT, live_gates


def test_live_gates_fail_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)
    out = live_gates(confirm_live=False, risk_ack="", paper_days=0, micro_live_days=0)
    assert not out["live_allowed"]
    assert "env_live_enabled" in out["failed"]


def test_live_gates_pass(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "true")
    out = live_gates(confirm_live=True, risk_ack=RISK_ACK_TEXT, paper_days=45, micro_live_days=45)
    assert out["live_allowed"]
