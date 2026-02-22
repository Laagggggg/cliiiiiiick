from pathlib import Path

from omega_quant.ops.ui_artifacts import artifact_target
from omega_quant.paper_account.db import get_paper_days_completed, register_paper_day
from omega_quant.time.market_hours import is_rth, should_block_new_orders


def test_market_hours_rth_gate():
    assert should_block_new_orders("2026-01-05T14:00:00Z")
    assert not should_block_new_orders("2026-01-05T15:00:00Z")
    assert should_block_new_orders("2026-01-05T22:00:00Z")
    assert is_rth("2026-01-05T15:00:00Z")


def test_unique_paper_day_counting(tmp_path):
    db = tmp_path / "paper.sqlite"
    assert register_paper_day("2026-01-05", str(db)) == 1
    assert register_paper_day("2026-01-05", str(db)) == 1
    assert register_paper_day("2026-01-06", str(db)) == 2
    assert get_paper_days_completed(str(db)) == 2


def test_artifact_target_blocks_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "equity_curve.png").write_bytes(b"x")
    assert artifact_target("/artifacts/equity_curve.png") == Path("artifacts/equity_curve.png")
    assert artifact_target("/artifacts/../../etc/passwd") is None
    assert artifact_target("/artifacts/not_allowed.png") is None
