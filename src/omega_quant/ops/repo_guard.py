from __future__ import annotations

from pathlib import Path


def ensure_repo_root_or_exit(entry_name: str) -> None:
    cwd = Path.cwd()
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        return

    hint_root = Path(__file__).resolve().parents[3]
    print(f"HALT: {entry_name} must be launched from repository root (pyproject.toml not found).")
    print(f'NEXT_ACTION: PowerShell -> cd "{hint_root}"; python {entry_name}')
    raise SystemExit(1)
