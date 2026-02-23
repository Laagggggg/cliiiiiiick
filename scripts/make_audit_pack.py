from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


def _write_checksums(root: Path) -> None:
    lines = []
    for fp in sorted(root.rglob("*")):
        if fp.is_file():
            h = hashlib.sha256(fp.read_bytes()).hexdigest()
            lines.append(f"{h}  {fp.relative_to(root)}")
    (root / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = Path.cwd()
    artifacts = base / "artifacts"
    out = base / "dist"
    artifacts.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    tmp = out / "audit_pack_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    include = [
        "paper_account.sqlite",
        "paper_cycle_result.json",
        "paper_proof_report.md",
        "paper_trade_reviews.md",
        "paper_ledger.json",
        "paper_trades.jsonl",
        "equity_curve.json",
        "equity_curve.png",
        "drawdown.png",
        "trade_markers.png",
        "doctor_report.json",
        "live_stream.jsonl",
        "recon_snapshots.jsonl",
        "daemon_tick_summary.jsonl",
        "live_monitor_acceptance.json",
        "live_ws_acceptance.json",
        "broker_daemon_acceptance.json",
        "ui_truth_contract_acceptance.json",
    ]

    included_files: list[str] = []
    missing_optional: list[str] = []
    for name in include:
        src = artifacts / name
        if src.exists() and src.is_file():
            shutil.copy2(src, tmp / name)
            included_files.append(name)
        else:
            missing_optional.append(name)

    rotated = sorted(artifacts.glob("live_stream_*.jsonl"))
    if rotated:
        idx = []
        for fp in rotated:
            shutil.copy2(fp, tmp / fp.name)
            idx.append(fp.name)
            included_files.append(fp.name)
        (tmp / "live_stream_rotations_index.json").write_text(json.dumps({"files": idx}, indent=2), encoding="utf-8")

    manifest = {
        "status": "ok",
        "base_dir": str(base),
        "included_files": included_files,
        "missing_optional_files": missing_optional,
    }
    (tmp / "audit_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_checksums(tmp)
    archive = shutil.make_archive(str(out / "paper_audit_pack"), "zip", tmp)
    shutil.rmtree(tmp)
    print(archive)


if __name__ == "__main__":
    main()
