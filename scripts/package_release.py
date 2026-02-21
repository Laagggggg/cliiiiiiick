from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
ZIP = OUT / "omega_quant_bundle"

INCLUDE = [
    "README.md",
    "pyproject.toml",
    "main_start.py",
    "main_ui.py",
    "main_paper.py",
    "main_validate.py",
    "main_report.py",
    "main_backtest.py",
    "main_live.py",
    "src",
    "tests",
]


def main() -> None:
    tmp = OUT / "bundle_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    for rel in INCLUDE:
        src = ROOT / rel
        dst = tmp / rel
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    archive = shutil.make_archive(str(ZIP), "zip", tmp)
    shutil.rmtree(tmp)
    print(f"Wrote {archive}")


if __name__ == "__main__":
    main()
