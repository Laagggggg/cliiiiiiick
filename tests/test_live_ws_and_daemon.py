from omega_quant.monitor import live_ws
from omega_quant.monitor.live_monitor import run_live_monitor
from omega_quant.ops import broker_paper_daemon as daemon


def test_websocket_dependency_declared():
    assert "websockets>=12.0" in open("pyproject.toml", "r", encoding="utf-8").read()


def test_websocket_happy_path_state_update():
    live_ws._ingest_raw({"T": "q", "S": "SPY", "bp": 100.0, "ap": 100.2, "t": "2026-01-01T00:00:00Z"})
    st = live_ws.get_ws_state()
    assert st["last_price"] == 100.2
    assert st["last_quote_ts"] == "2026-01-01T00:00:00Z"



def test_websocket_replay_correctness(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    live_ws._ingest_raw({"T": "q", "S": "SPY", "bp": 100.0, "ap": 100.2, "t": "2026-01-01T00:00:00Z"})
    live_ws._ingest_raw({"T": "t", "S": "SPY", "p": 100.3, "s": 10, "t": "2026-01-01T00:00:05Z"})
    live_ws._ingest_raw({"T": "b", "S": "SPY", "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.5, "v": 1000, "t": "2026-01-01T01:00:00Z"})
    out = live_ws.replay_stream()
    assert out["status"] == "ok"
    assert out["last_bar_ts"] == "2026-01-01T01:00:00Z"
    assert out["last_price"] == 100.5


def test_websocket_fallback_label_on_failure(monkeypatch):
    monkeypatch.setattr(
        "omega_quant.monitor.live_monitor.ensure_websocket",
        lambda symbol='SPY': {"ok": False, "transport": "REQUIRES ALPACA KEYS -> POLLING"},
    )
    monkeypatch.setattr(
        "omega_quant.monitor.live_monitor.get_ws_state",
        lambda: {"connected": False, "transport": "REQUIRES ALPACA KEYS -> POLLING", "last_price": None, "last_bar_ts": ""},
    )
    out = run_live_monitor(mode="websocket")
    assert "POLLING" in out["transport"]


def test_broker_daemon_checkpoint_skips_duplicate_bar(monkeypatch):
    class DummyBroker:
        def enabled(self): return True
        def list_positions(self): return []
        def list_orders(self, status='open', limit=50): return []
        def get_order_by_client_id(self, coid): return None
        def place_market_order(self, symbol, side, qty, client_order_id=None):
            return {"id": client_order_id or "x", "filled_qty": qty, "filled_avg_price": 100.0, "status": "filled"}
        def get_order(self, oid): return {"id": oid, "filled_qty": 1, "filled_avg_price": 100.0, "status": "filled"}

    class DummyProvider:
        def get_bars(self, symbol, timeframe, limit=120):
            ts = "2026-01-01T00:00:00Z"
            return [type('B', (), {"timestamp": ts, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000000}) for _ in range(limit)]

    cp = {"v": None}
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.close_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_order_event", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_recon_snapshot", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.export_recon_jsonl", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_account_summary", lambda *a, **k: {"equity": 5000, "cash": 5000})
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_equity_point", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_checkpoint", lambda *a, **k: cp["v"])
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.set_checkpoint", lambda *a, **k: cp.__setitem__("v", a[1]))
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.run_step", lambda *a, **k: {"status": "NO_TRADE", "reason": "x"})

    a = daemon._step_once(DummyBroker(), DummyProvider())
    b = daemon._step_once(DummyBroker(), DummyProvider())
    assert a["status"] == "NO_TRADE"
    assert b["status"] == "SKIP"


def test_broker_recon_mismatch_halts(monkeypatch):
    class DummyBroker:
        def enabled(self): return True
        def list_positions(self): return [{"symbol": "SPY", "qty": "2"}]
        def list_orders(self, status='open', limit=50): return []
        def get_order_by_client_id(self, coid): return None
        def place_market_order(self, symbol, side, qty, client_order_id=None): return {"id": "x"}
        def get_order(self, oid): return {"id": oid}

    class DummyProvider:
        def get_bars(self, symbol, timeframe, limit=120):
            return [type('B', (), {"timestamp": f"2026-01-01T00:{i%60:02d}:00Z", "open": 100+i*0.01, "high": 101+i*0.01, "low": 99+i*0.01, "close": 100+i*0.01, "volume": 1000000}) for i in range(limit)]

    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_account_summary", lambda *a, **k: {"equity": 5000, "cash": 5000})
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_equity_point", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_recon_snapshot", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.export_recon_jsonl", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_checkpoint", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.set_checkpoint", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.run_step", lambda *a, **k: {"status": "NO_TRADE", "reason": "x"})

    out = daemon._step_once(DummyBroker(), DummyProvider())
    assert out["status"] == "HALT"
    assert out["reason"] == "RECON_MISMATCH"


def test_websocket_journal_schema_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    live_ws._ingest_raw({"T": "q", "S": "SPY", "bp": 100.0, "ap": 100.2, "t": "2026-01-01T00:00:00Z"})
    line = open("artifacts/live_stream.jsonl", "r", encoding="utf-8").read().strip().splitlines()[-1]
    import json
    row = json.loads(line)
    assert row["schema"] == "alpaca.marketdata.v2"
    assert row["kind"] == "quote"
    assert row["event_ts"] == "2026-01-01T00:00:00Z"


def test_websocket_mock_server_frames(tmp_path, monkeypatch):
    import asyncio
    import json

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_API_SECRET", "s")

    class FakeWS:
        async def send(self, _msg):
            return None

        def __aiter__(self):
            payloads = [
                json.dumps([{"T": "q", "S": "SPY", "bp": 100.0, "ap": 100.2, "t": "2026-01-01T00:00:00Z"}]),
                json.dumps([{"T": "t", "S": "SPY", "p": 100.3, "s": 10, "t": "2026-01-01T00:00:05Z"}]),
                json.dumps([{"T": "b", "S": "SPY", "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.5, "v": 1000, "t": "2026-01-01T01:00:00Z"}]),
            ]

            async def gen():
                for row in payloads:
                    yield row

            return gen()

    class FakeConn:
        async def __aenter__(self):
            return FakeWS()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeWebsockets:
        @staticmethod
        def connect(*_a, **_k):
            return FakeConn()

    import sys

    sys.modules["websockets"] = FakeWebsockets
    asyncio.run(live_ws._run_ws("SPY", max_messages=3))

    st = live_ws.get_ws_state()
    assert st["last_quote_ts"] == "2026-01-01T00:00:00Z"
    assert st["last_trade_ts"] == "2026-01-01T00:00:05Z"
    assert st["last_bar_ts"] == "2026-01-01T01:00:00Z"


def test_normalize_event_schema_fields():
    ev = live_ws._normalize_event({"T": "b", "S": "SPY", "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 12, "t": "2026-01-01T01:00:00Z"})
    assert ev is not None
    assert ev["schema"] == "alpaca.marketdata.v2"
    assert ev["kind"] == "bar"
    assert ev["symbol"] == "SPY"
    assert ev["price"] == 100.5


def test_provider_cache_fallback(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    class BadProvider:
        def source_name(self):
            return "bad"

        def get_bars(self, *_a, **_k):
            raise RuntimeError("down")

    class GoodProvider:
        def source_name(self):
            return "stooq_daily"

        def get_bars(self, *_a, **_k):
            return [type("B", (), {"timestamp": "2026-01-01T00:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1})]

        def get_quote(self, *_a, **_k):
            return type("Q", (), {"ask": 100.5})

    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [GoodProvider()])
    out_ok = run_live_monitor(mode="polling")
    assert out_ok["status"] in {"ok", "HALT"}

    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [BadProvider()])
    out = run_live_monitor(mode="polling")
    assert out["data_grade"] == "CACHED"
    assert out["mode_truth"] == "SAFE_DEGRADED"
    assert "cached bars" in out["decision_sentence"]


def test_broker_recon_warn_with_open_orders(monkeypatch):
    class DummyBroker:
        def enabled(self): return True
        def list_positions(self): return [{"symbol":"SPY","qty":"2"}]
        def list_orders(self, status="open", limit=50): return [{"id":"o1"}]
        def get_order_by_client_id(self, coid): return None
        def place_market_order(self, *a, **k): return {"id":"x"}
        def get_order(self, oid): return {"id":oid}

    class DummyProvider:
        def get_bars(self, symbol, timeframe, limit=120):
            return [type("B", (), {"timestamp":"2026-01-01T00:00:00Z","open":100.0,"high":101.0,"low":99.0,"close":100.0,"volume":1}) for _ in range(limit)]

    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_open_position", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_account_summary", lambda *a, **k: {"equity": 5000, "cash": 5000})
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_equity_point", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.get_checkpoint", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.set_checkpoint", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_order_event", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.append_recon_snapshot", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.export_recon_jsonl", lambda *a, **k: None)
    monkeypatch.setattr("omega_quant.ops.broker_paper_daemon.run_step", lambda *a, **k: {"status": "NO_TRADE", "reason": "x"})
    out = daemon._step_once(DummyBroker(), DummyProvider())
    assert out["reconciliation"]["status"] == "WARN"



def test_alpaca_provider_data_grade_not_fallback(monkeypatch):
    class AlpacaLike:
        def source_name(self): return "alpaca"
        def get_bars(self, *_a, **_k):
            return [type("B", (), {"timestamp":"2026-01-01T00:00:00Z","open":1.0,"high":1.0,"low":1.0,"close":1.0,"volume":1})]
        def get_quote(self, *_a, **_k):
            return type("Q", (), {"ask":1.0})

    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [AlpacaLike()])
    out = run_live_monitor(mode="polling")
    assert out["data_grade"] != "FALLBACK_POLLING"
    assert out["provider_primary"] if "provider_primary" in out else True


def test_websocket_preferred_timestamp(monkeypatch):
    class AlpacaLike:
        def source_name(self): return "alpaca"
        def get_bars(self, *_a, **_k):
            return [type("B", (), {"timestamp":"2026-01-01T00:00:00Z","open":1.0,"high":1.0,"low":1.0,"close":1.0,"volume":1})]
        def get_quote(self, *_a, **_k):
            return type("Q", (), {"ask":1.0})

    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_provider_chain", lambda: [AlpacaLike()])
    monkeypatch.setattr("omega_quant.monitor.live_monitor.ensure_websocket", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr("omega_quant.monitor.live_monitor.get_ws_state", lambda: {"connected": True, "last_price": 2.0, "last_bar_ts": "2026-01-01T02:00:00Z", "last_quote_ts": "2026-01-01T02:00:01Z", "last_trade_ts": "", "last_event_kind": "quote", "stall_seconds": 0})
    out = run_live_monitor(mode="websocket")
    assert out["transport"] == "WEBSOCKET"
    assert out["last_bar_ts"] == "2026-01-01T02:00:00Z"

