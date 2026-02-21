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
                initial_equity REAL NOT NULL,
                cash REAL NOT NULL,
                equity REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
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
                realized REAL NOT NULL,
                unrealized REAL NOT NULL,
                drawdown REAL NOT NULL
            );
            """
        )


def get_or_create_account(starting_capital: float, db_path: str = DB_DEFAULT) -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT account_id,initial_equity,cash,equity,realized_pnl,unrealized_pnl FROM account_state WHERE account_id='paper'").fetchone()
        if row:
            return {
                "account_id": row[0],
                "initial_equity": float(row[1]),
                "cash": float(row[2]),
                "equity": float(row[3]),
                "realized_pnl": float(row[4]),
                "unrealized_pnl": float(row[5]),
            }

        conn.execute(
            "INSERT INTO account_state(account_id,initial_equity,cash,equity,realized_pnl,unrealized_pnl,updated_at) VALUES('paper',?,?,?,?,0,datetime('now'))",
            (starting_capital, starting_capital, starting_capital, 0),
        )
        conn.execute(
            "INSERT INTO equity_curve(ts,equity,cash,realized,unrealized,drawdown) VALUES('1970-01-01T00:00:00Z',?,?,0,0,0)",
            (starting_capital, starting_capital),
        )
    return get_or_create_account(starting_capital, db_path)


def reset_account(starting_capital: float, db_path: str = DB_DEFAULT) -> dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM fills")
        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM positions")
        conn.execute("DELETE FROM equity_curve")
        conn.execute("DELETE FROM account_state WHERE account_id='paper'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('fills','trades','equity_curve')")
    return get_or_create_account(starting_capital, db_path)


def _mark_to_market(conn: sqlite3.Connection, ts: str, mark_price: float) -> None:
    pos = conn.execute("SELECT qty,avg_entry FROM positions WHERE symbol='SPY'").fetchone()
    unrealized = 0.0
    if pos:
        qty, avg = float(pos[0]), float(pos[1])
        unrealized = (mark_price - avg) * qty
        conn.execute("UPDATE positions SET last_price=?, unrealized_pnl=?, updated_at=datetime('now') WHERE symbol='SPY'", (mark_price, unrealized))
    acct = conn.execute("SELECT cash,realized_pnl,initial_equity FROM account_state WHERE account_id='paper'").fetchone()
    cash, realized, _ = float(acct[0]), float(acct[1]), float(acct[2])
    equity = cash + unrealized
    conn.execute("UPDATE account_state SET equity=?, unrealized_pnl=?, updated_at=datetime('now') WHERE account_id='paper'", (equity, unrealized))
    peak = float(conn.execute("SELECT COALESCE(MAX(equity), ?) FROM equity_curve", (equity,)).fetchone()[0])
    dd = equity - peak
    conn.execute("INSERT INTO equity_curve(ts,equity,cash,realized,unrealized,drawdown) VALUES(?,?,?,?,?,?)", (ts, equity, cash, realized, unrealized, dd))


def open_position(ts: str, symbol: str, qty: float, price: float, fee: float, db_path: str = DB_DEFAULT) -> None:
    with _connect(db_path) as conn:
        conn.execute("BEGIN")
        cash = float(conn.execute("SELECT cash FROM account_state WHERE account_id='paper'").fetchone()[0])
        conn.execute("UPDATE account_state SET cash=? WHERE account_id='paper'", (cash - fee,))
        conn.execute(
            "INSERT INTO positions(symbol,qty,avg_entry,last_price,unrealized_pnl,updated_at) VALUES(?,?,?,?,0,datetime('now')) "
            "ON CONFLICT(symbol) DO UPDATE SET qty=excluded.qty, avg_entry=excluded.avg_entry, last_price=excluded.last_price, updated_at=datetime('now')",
            (symbol, qty, price, price),
        )
        conn.execute("INSERT INTO fills(trade_id,ts,symbol,side,qty,price,fee) VALUES(NULL,?,?,?,?,?,?)", (ts, symbol, "BUY", qty, price, fee))
        _mark_to_market(conn, ts, price)
        conn.commit()


def close_position(ts: str, symbol: str, price: float, fee: float, reason: dict[str, Any], db_path: str = DB_DEFAULT) -> dict[str, Any] | None:
    with _connect(db_path) as conn:
        pos = conn.execute("SELECT qty,avg_entry FROM positions WHERE symbol=?", (symbol,)).fetchone()
        if not pos:
            return None
        qty, entry = float(pos[0]), float(pos[1])
        pnl_gross = (price - entry) * qty
        pnl_net = pnl_gross - fee
        conn.execute("BEGIN")
        conn.execute("INSERT INTO trades(ts_open,ts_close,symbol,side,qty,entry,exit,pnl_gross,pnl_net,reason_json) VALUES(?,?,?,?,?,?,?,?,?,?)", (ts, ts, symbol, "LONG", qty, entry, price, pnl_gross, pnl_net, json.dumps(reason, sort_keys=True)))
        trade_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute("INSERT INTO fills(trade_id,ts,symbol,side,qty,price,fee) VALUES(?,?,?,?,?,?,?)", (trade_id, ts, symbol, "SELL", qty, price, fee))
        conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
        acct = conn.execute("SELECT cash,realized_pnl FROM account_state WHERE account_id='paper'").fetchone()
        cash_after = float(acct[0]) + pnl_net
        realized_after = float(acct[1]) + pnl_net
        conn.execute("UPDATE account_state SET cash=?, realized_pnl=? WHERE account_id='paper'", (cash_after, realized_after))
        _mark_to_market(conn, ts, price)
        conn.commit()
    return {"trade_id": trade_id, "pnl_dollars": pnl_net}


def append_equity_point(ts: str, last_price: float, db_path: str = DB_DEFAULT) -> None:
    with _connect(db_path) as conn:
        _mark_to_market(conn, ts, last_price)


def has_open_position(symbol: str = "SPY", db_path: str = DB_DEFAULT) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM positions WHERE symbol=?", (symbol,)).fetchone()
        return bool(row)


def get_open_position(symbol: str = "SPY", db_path: str = DB_DEFAULT) -> dict[str, Any] | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT qty,avg_entry,last_price FROM positions WHERE symbol=?", (symbol,)).fetchone()
        if not row:
            return None
        return {"qty": float(row[0]), "avg_entry": float(row[1]), "last_price": float(row[2])}


def list_trades(db_path: str = DB_DEFAULT) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT trade_id,ts_close,symbol,side,qty,entry,exit,pnl_net,reason_json FROM trades ORDER BY trade_id").fetchall()
    return [{"trade_id": int(r[0]), "timestamp": r[1], "symbol": r[2], "side": r[3], "qty": float(r[4]), "entry": float(r[5]), "exit": float(r[6]), "pnl_dollars": float(r[7]), "reason": json.loads(r[8])} for r in rows]


def list_equity_curve(db_path: str = DB_DEFAULT) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT ts,equity,cash,realized,unrealized,drawdown FROM equity_curve ORDER BY seq").fetchall()
    return [{"ts": r[0], "equity": float(r[1]), "cash": float(r[2]), "realized": float(r[3]), "unrealized": float(r[4]), "drawdown": float(r[5])} for r in rows]


def get_account_summary(db_path: str = DB_DEFAULT) -> dict[str, Any]:
    acct = get_or_create_account(5000.0, db_path)
    trades = list_trades(db_path)
    wins = [t["pnl_dollars"] for t in trades if t["pnl_dollars"] > 0]
    losses = [t["pnl_dollars"] for t in trades if t["pnl_dollars"] < 0]
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    win_rate = len(wins) / len(trades) if trades else 0.0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss) if trades else 0.0
    pf = (sum(wins) / abs(sum(losses))) if losses else 0.0
    return {
        **acct,
        "trade_count": len(trades),
        "win_rate_pct": win_rate * 100.0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "profit_factor": pf,
        "return_pct": ((acct["equity"] - acct["initial_equity"]) / acct["initial_equity"] * 100.0) if acct["initial_equity"] else 0.0,
    }


def export_jsonl(path: str = "artifacts/paper_trades.jsonl", db_path: str = DB_DEFAULT) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for t in list_trades(db_path):
            f.write(json.dumps(t, sort_keys=True) + "\n")
    return str(p)
