from omega_quant.ops.repo_guard import ensure_repo_root_or_exit


def test_repo_guard_halts_outside_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    try:
        ensure_repo_root_or_exit("main_ui.py")
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1
