from pathlib import Path

from omega_quant.ops.trade_review import append_trade_review, render_trade_reviews_markdown


def test_trade_review_files(tmp_path: Path):
    jsonl = tmp_path / "paper_trades.jsonl"
    md = tmp_path / "paper_trade_reviews.md"

    append_trade_review(str(jsonl), {"status": "TRADE", "score": 0.8, "threshold": 0.5, "reason": "entry_signal_passed"})
    append_trade_review(str(jsonl), {"status": "NO_TRADE", "score": 0.3, "threshold": 0.5, "reason": "below_threshold"})
    render_trade_reviews_markdown(str(jsonl), str(md))

    txt = md.read_text(encoding="utf-8")
    assert "Paper Trade Reviews" in txt
    assert "TRADE" in txt
    assert "NO_TRADE" in txt
