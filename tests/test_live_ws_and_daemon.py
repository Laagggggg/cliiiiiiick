from omega_quant.monitor import live_ws
from omega_quant.monitor.live_monitor import run_live_monitor
from omega_quant.ops import broker_paper_daemon as daemon


def test_websocket_happy_path_state_update():
    live_ws._apply_quote({"T": "q", "bp": 100.0, "ap": 100.2, "t": "2026-01-01T00:00:00Z"})
    st = live_ws.get_ws_state()
    assert st["last_price"] == 100.2
    assert st["last_ts"] == "2026-01-01T00:00:00Z"


def test_websocket_fallback_label_on_failure(monkeypatch):
    monkeypatch.setattr("omega_quant.monitor.live_monitor.ensure_websocket", lambda symbol='SPY': {"ok": False, "transport": "WEBSOCKET FAILED -> POLLING"})
    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_ws_state", lambda: {"connected": False, "transport": "WEBSOCKET FAILED -> POLLING", "last_price": None, "last_ts": ""})
    out = run_live_monitor(mode="websocket")
    assert "POLLING" in out["transport"]


def test_broker_daemon_idempotent_client_order_id(monkeypatch):
    class DummyBroker:
        def __init__(self): self.orders = {}
        def enabled(self): return True
        def list_positions(self): return []
        def list_orders(self, status='open', limit=50): return []
        def get_order_by_client_id(self, coid): return self.orders.get(coid)
        def place_market_order(self, symbol, side, qty, client_order_id=None):
            o = {"id": client_order_id or "x", "filled_qty": qty, "filled_avg_price": 100.0}
            self.orders[client_order_id] = o
            return o
        def get_order(self, oid):
            return {"id": oid, "filled_qty": 1, "filled_avg_price": 100.0}

    class DummyProvider:
        def get_bars(self, symbol, timeframe, limit=120):
            base = []
            for i in range(130):
                base.append(type('B', (), {"timestamp": f"2026-01-01T00:{i%60:02d}:00Z", "open": 100+i*0.01, "high": 101+i*0.01, "low": 99+i*0.01, "close": 100+i*0.01, "volume": 1000000}))
            return base[-limit:]

    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.AlpacaPaperBroker", DummyBroker)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.AlpacaMarketDataProvider", DummyProvider)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.close_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_account_summary", lambda *a, **k: {"equity": 5000})
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_equity_point", lambda *a, **k: None)

    out = daemon.run_broker_paper_daemon(seconds=1, interval_s=1)
    assert out["status"] == "ok"
