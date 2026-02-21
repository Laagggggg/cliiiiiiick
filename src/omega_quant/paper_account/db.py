from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def _connect(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(p)


def init_db(db_path: str = "artifacts/paper_account.sqlite3") -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS account_state (
                account_id TEXT PRIMARY KEY,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                entry REAL NOT NULL,
                exit REAL NOT NULL,
                pnl_net REAL NOT NULL,
                equity_before REAL NOT NULL,
                equity_after REAL NOT NULL,
                reason_json TEXT NOT NULL
            )
            """
        )


def get_or_create_account(starting_capital: float, db_path: str = "artifacts/paper_account.sqlite3") -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT account_id, equity, cash, updated_at FROM account_state WHERE account_id='paper'")
        row = cur.fetchone()
        if row:
            return {"account_id": row[0], "equity": float(row[1]), "cash": float(row[2]), "updated_at": row[3]}

        conn.execute(
            "INSERT INTO account_state(account_id,equity,cash,updated_at) VALUES('paper',?,?,datetime('now'))",
            (starting_capital, starting_capital),
        )
        return {"account_id": "paper", "equity": float(starting_capital), "cash": float(starting_capital), "updated_at": "now"}


def reset_account(starting_capital: float, db_path: str = "artifacts/paper_account.sqlite3") -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM account_state WHERE account_id='paper'")
        conn.execute(
            "INSERT INTO account_state(account_id,equity,cash,updated_at) VALUES('paper',?,?,datetime('now'))",
            (starting_capital, starting_capital),
        )
    return {"account_id": "paper", "equity": float(starting_capital), "cash": float(starting_capital)}


def apply_fill(
    *,
    ts: str,
    symbol: str,
    side: str,
    qty: float,
    entry: float,
    exit: float,
    pnl_net: float,
    reason: dict[str, Any],
    db_path: str = "artifacts/paper_account.sqlite3",
) -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT equity FROM account_state WHERE account_id='paper'")
        row = cur.fetchone()
        if not row:
            raise RuntimeError("paper account not initialized")
        equity_before = float(row[0])
        equity_after = equity_before + float(pnl_net)

        conn.execute(
            """
            INSERT INTO trades(ts,symbol,side,qty,entry,exit,pnl_net,equity_before,equity_after,reason_json)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (ts, symbol, side, qty, entry, exit, pnl_net, equity_before, equity_after, json.dumps(reason, sort_keys=True)),
        )
        conn.execute(
            "UPDATE account_state SET equity=?, cash=?, updated_at=datetime('now') WHERE account_id='paper'",
            (equity_after, equity_after),
        )

    return {"equity_before": equity_before, "equity_after": equity_after}


def list_trades(db_path: str = "artifacts/paper_account.sqlite3") -> list[dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT trade_id, ts, symbol, side, qty, entry, exit, pnl_net, equity_before, equity_after, reason_json FROM trades ORDER BY trade_id"
        ).fetchall()
    return [
        {
            "trade_id": int(r[0]),
            "timestamp": r[1],
            "symbol": r[2],
            "side": r[3],
            "qty": float(r[4]),
            "entry": float(r[5]),
            "exit": float(r[6]),
            "pnl_dollars": float(r[7]),
            "equity_before": float(r[8]),
            "equity_after": float(r[9]),
            "reason": json.loads(r[10]),
        }
        for r in rows
    ]


def get_account_summary(db_path: str = "artifacts/paper_account.sqlite3") -> dict[str, Any]:
    acct = get_or_create_account(5000.0, db_path=db_path)
    trades = list_trades(db_path=db_path)
    wins = sum(1 for t in trades if t["pnl_dollars"] > 0)
    return {
        "account_id": acct["account_id"],
        "equity": acct["equity"],
        "trade_count": len(trades),
        "wins": wins,
        "win_rate_pct": (wins / len(trades) * 100.0) if trades else 0.0,
    }


def export_jsonl(path: str = "artifacts/paper_trades.jsonl", db_path: str = "artifacts/paper_account.sqlite3") -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    trades = list_trades(db_path=db_path)
    with p.open("w", encoding="utf-8") as f:
        for t in trades:
            f.write(json.dumps(t, sort_keys=True) + "\n")
    return str(p)
