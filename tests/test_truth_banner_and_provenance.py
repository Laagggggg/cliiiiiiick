from pathlib import Path

from omega_quant.ui_service import run_action


def test_startup_truth_not_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action("paper_account")
    assert out["data_grade"] in {"CSV_SAMPLE", "CACHED", "FALLBACK_POLLING"}
    assert "UNKNOWN" not in out["data_grade"]


def test_provenance_never_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action("paper_account")
    prov = out.get("provenance", {})
    assert isinstance(prov, dict)
    assert len(prov) > 0
    for k in ["provider_primary", "data_grade", "freshness_label", "freshness_basis", "recon_status"]:
        assert k in prov


def test_main_ui_has_sparkline_overlay_text():
    txt = Path("main_ui.py").read_text(encoding="utf-8")
    assert "No live ticks yet — run Live Monitor (Polling/Websocket)." in txt
