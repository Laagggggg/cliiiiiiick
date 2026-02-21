from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "artifacts/paper_account.sqlite"


def _connect(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: str = DB_DEFAULT) -> None:
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS account_state (
                account_id TEXT PRIMARY KEY,
                cash REAL NOT NULL,
                equity REAL NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                qty REAL NOT NULL,
                avg_entry REAL NOT NULL,
                last_price REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fills (
                fill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_open TEXT NOT NULL,
                ts_close TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                entry REAL NOT NULL,
                exit REAL NOT NULL,
                pnl_gross REAL NOT NULL,
                pnl_net REAL NOT NULL,
                reason_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS equity_curve (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                unrealized REAL NOT NULL,
                realized REAL NOT NULL,
                drawdown REAL NOT NULL
            );
            """
        )


def get_or_create_account(starting_capital: float, db_path: str = DB_DEFAULT) -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT account_id,cash,equity,realized_pnl,updated_at FROM account_state WHERE account_id='paper'").fetchone()
        if row:
            return {"account_id": row[0], "cash": float(row[1]), "equity": float(row[2]), "realized_pnl": float(row[3]), "updated_at": row[4]}
        conn.execute(
            "INSERT INTO account_state(account_id,cash,equity,realized_pnl,updated_at) VALUES('paper',?,?,0,datetime('now'))",
            (starting_capital, starting_capital),
        )
        conn.execute(
            "INSERT INTO equity_curve(ts,equity,cash,unrealized,realized,drawdown) VALUES('1970-01-01T00:00:00Z',?,?,0,0,0)",
            (starting_capital, starting_capital),
        )
        return {"account_id": "paper", "cash": float(starting_capital), "equity": float(starting_capital), "realized_pnl": 0.0, "updated_at": "now"}


def reset_account(starting_capital: float, db_path: str = DB_DEFAULT) -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM fills")
        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM positions")
        conn.execute("DELETE FROM equity_curve")
        conn.execute("DELETE FROM account_state WHERE account_id='paper'")
        conn.execute(
            "INSERT INTO account_state(account_id,cash,equity,realized_pnl,updated_at) VALUES('paper',?,?,0,datetime('now'))",
            (starting_capital, starting_capital),
        )
        conn.execute(
            "INSERT INTO equity_curve(ts,equity,cash,unrealized,realized,drawdown) VALUES('1970-01-01T00:00:00Z',?,?,0,0,0)",
            (starting_capital, starting_capital),
        )
    return {"account_id": "paper", "cash": float(starting_capital), "equity": float(starting_capital)}


def append_equity_point(ts: str, last_price: float, db_path: str = DB_DEFAULT) -> None:
    init_db(db_path)
    with _connect(db_path) as conn:
        acct = conn.execute("SELECT cash, realized_pnl FROM account_state WHERE account_id='paper'").fetchone()
        cash = float(acct[0]) if acct else 0.0
        realized = float(acct[1]) if acct else 0.0
        pos = conn.execute("SELECT qty, avg_entry FROM positions WHERE symbol='SPY'").fetchone()
        unrealized = 0.0
        if pos:
            qty = float(pos[0])
            avg_entry = float(pos[1])
            unrealized = (last_price - avg_entry) * qty
            conn.execute(
                "UPDATE positions SET last_price=?, unrealized_pnl=?, updated_at=datetime('now') WHERE symbol='SPY'",
                (last_price, unrealized),
            )
        equity = cash + unrealized
        peak = conn.execute("SELECT COALESCE(MAX(equity), ?) FROM equity_curve", (equity,)).fetchone()[0]
        drawdown = equity - float(peak)
        conn.execute(
            "UPDATE account_state SET equity=?, updated_at=datetime('now') WHERE account_id='paper'",
            (equity,),
        )
        conn.execute(
            "INSERT INTO equity_curve(ts,equity,cash,unrealized,realized,drawdown) VALUES(?,?,?,?,?,?)",
            (ts, equity, cash, unrealized, realized, drawdown),
        )


def record_round_trip(
    *,
    ts_open: str,
    ts_close: str,
    symbol: str,
    qty: float,
    entry: float,
    exit: float,
    fee: float,
    reason: dict[str, Any],
    db_path: str = DB_DEFAULT,
) -> dict[str, Any]:
    init_db(db_path)
    pnl_gross = (exit - entry) * qty
    pnl_net = pnl_gross - fee

    with _connect(db_path) as conn:
        cash_row = conn.execute("SELECT cash, realized_pnl FROM account_state WHERE account_id='paper'").fetchone()
        if not cash_row:
            raise RuntimeError("paper account not initialized")
        cash_before = float(cash_row[0])
        realized_before = float(cash_row[1])
        cash_after = cash_before + pnl_net
        realized_after = realized_before + pnl_net

        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO trades(ts_open,ts_close,symbol,side,qty,entry,exit,pnl_gross,pnl_net,reason_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (ts_open, ts_close, symbol, "LONG", qty, entry, exit, pnl_gross, pnl_net, json.dumps(reason, sort_keys=True)),
        )
        trade_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute(
            "INSERT INTO fills(trade_id,ts,symbol,side,qty,price,fee) VALUES(?,?,?,?,?,?,?)",
            (trade_id, ts_open, symbol, "BUY", qty, entry, fee / 2),
        )
        conn.execute(
            "INSERT INTO fills(trade_id,ts,symbol,side,qty,price,fee) VALUES(?,?,?,?,?,?,?)",
            (trade_id, ts_close, symbol, "SELL", qty, exit, fee / 2),
        )
        conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
        conn.execute(
            "UPDATE account_state SET cash=?, equity=?, realized_pnl=?, updated_at=datetime('now') WHERE account_id='paper'",
            (cash_after, cash_after, realized_after),
        )
        conn.execute(
            "INSERT INTO equity_curve(ts,equity,cash,unrealized,realized,drawdown) VALUES(?,?,?,?,?,0)",
            (ts_close, cash_after, cash_after, 0.0, realized_after),
        )
        conn.commit()

    return {"trade_id": trade_id, "pnl_dollars": pnl_net}


def list_trades(db_path: str = DB_DEFAULT) -> list[dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT trade_id,ts_open,ts_close,symbol,side,qty,entry,exit,pnl_net,reason_json FROM trades ORDER BY trade_id"
        ).fetchall()
    return [
        {
            "trade_id": int(r[0]),
            "timestamp": r[2],
            "symbol": r[3],
            "side": r[4],
            "qty": float(r[5]),
            "entry": float(r[6]),
            "exit": float(r[7]),
            "pnl_dollars": float(r[8]),
            "reason": json.loads(r[9]),
        }
        for r in rows
    ]


def list_equity_curve(db_path: str = DB_DEFAULT) -> list[dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT ts,equity,cash,unrealized,realized,drawdown FROM equity_curve ORDER BY seq").fetchall()
    return [{"ts": r[0], "equity": float(r[1]), "cash": float(r[2]), "unrealized": float(r[3]), "realized": float(r[4]), "drawdown": float(r[5])} for r in rows]


def get_account_summary(db_path: str = DB_DEFAULT) -> dict[str, Any]:
    acct = get_or_create_account(5000.0, db_path=db_path)
    trades = list_trades(db_path=db_path)
    wins = sum(1 for t in trades if t["pnl_dollars"] > 0)
    realized = float(acct.get("realized_pnl", 0.0))
    return {
        "account_id": acct["account_id"],
        "equity": acct["equity"],
        "cash": acct["cash"],
        "realized_pnl": realized,
        "unrealized_pnl": acct["equity"] - acct["cash"],
        "trade_count": len(trades),
        "wins": wins,
        "win_rate_pct": (wins / len(trades) * 100.0) if trades else 0.0,
    }


def export_jsonl(path: str = "artifacts/paper_trades.jsonl", db_path: str = DB_DEFAULT) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    trades = list_trades(db_path=db_path)
    with p.open("w", encoding="utf-8") as f:
        for t in trades:
            f.write(json.dumps(t, sort_keys=True) + "\n")
    return str(p)
