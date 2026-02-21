from __future__ import annotations

import subprocess


def run(cmd: str) -> tuple[bool, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip()
    return p.returncode == 0, out


def main() -> int:
    checks = [
        ("tests", "pytest -q"),
        ("compile", "python -m py_compile $(rg --files -g '*.py')"),
        ("validate", "PYTHONPATH=src python main_validate.py"),
        ("paper", "PYTHONPATH=src python main_paper.py --capital 3000 --cycles 2"),
        ("proof", "PYTHONPATH=src python - <<'PY'\nfrom omega_quant.ops.proof_check import verify_paper_result\nprint(verify_paper_result())\nPY"),
    ]
    all_ok = True
    for name, cmd in checks:
        ok, out = run(cmd)
        print(f"[{name}] {'PASS' if ok else 'FAIL'}")
        print(out)
        print("-" * 60)
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
