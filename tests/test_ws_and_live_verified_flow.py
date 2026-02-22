import json
from pathlib import Path

from omega_quant.ui_service import run_action


def test_make_live_verified_halts_without_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    out = run_action("make_live_verified")
    assert out["status"] == "HALT"
    assert "Next:" in out["decision_sentence"]


def test_live_ws_acceptance_schema(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import subprocess, sys

    rc = subprocess.run([sys.executable, "scripts/live_ws_acceptance.py", "--seconds", "1"], cwd=Path(__file__).resolve().parents[1]).returncode
    assert rc == 0
    p = Path(__file__).resolve().parents[1] / "artifacts" / "live_ws_acceptance.json"
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert "status" in payload
    assert "reason" in payload
    assert "next_action" in payload
    assert "metrics" in payload
