from __future__ import annotations

import shutil
from pathlib import Path


ARTIFACTS = Path("artifacts")
OUT = Path("dist")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "audit_pack_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    include = [
        "paper_account.sqlite3",
        "paper_cycle_result.json",
        "paper_proof_report.md",
        "paper_trade_reviews.md",
        "paper_ledger.json",
        "paper_trades.jsonl",
        "checksums.sha256",
    ]
    for name in include:
        src = ARTIFACTS / name
        if src.exists():
            shutil.copy2(src, tmp / name)

    archive = shutil.make_archive(str(OUT / "paper_audit_pack"), "zip", tmp)
    shutil.rmtree(tmp)
    print(archive)


if __name__ == "__main__":
    main()
