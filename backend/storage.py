"""SQLite storage for account data.

Everything lives in one local file (DB_PATH in .env, default data/portfolio.db).
All saves are idempotent: running sync twice never creates duplicate rows.
"""
import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    exec_id      TEXT PRIMARY KEY,
    time         TEXT NOT NULL,      -- ISO timestamp (UTC)
    con_id       INTEGER NOT NULL,
    symbol       TEXT NOT NULL,
    sec_type     TEXT,
    currency     TEXT,
    side         TEXT,               -- BOT or SLD
    shares       REAL NOT NULL,
    price        REAL NOT NULL,
    commission   REAL,
    realized_pnl REAL                -- IB's figure; NULL for opening trades
);
CREATE TABLE IF NOT EXISTS nav_daily (
    date                 TEXT PRIMARY KEY,   -- YYYY-MM-DD
    net_liquidation      REAL NOT NULL,
    total_cash           REAL,
    gross_position_value REAL,
    unrealized_pnl       REAL,
    realized_pnl         REAL,
    currency             TEXT
);
CREATE TABLE IF NOT EXISTS cash_flows (
    date   TEXT PRIMARY KEY,
    amount REAL NOT NULL             -- deposits positive, withdrawals negative
);
CREATE TABLE IF NOT EXISTS positions_daily (
    date         TEXT NOT NULL,
    con_id       INTEGER NOT NULL,
    symbol       TEXT NOT NULL,
    quantity     REAL NOT NULL,
    avg_cost     REAL,
    market_price REAL,
    market_value REAL,
    currency     TEXT,
    PRIMARY KEY (date, con_id)
);
CREATE TABLE IF NOT EXISTS prices_daily (
    con_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    date   TEXT NOT NULL,
    close  REAL NOT NULL,            -- adjusted for splits and dividends
    PRIMARY KEY (con_id, date)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the database, creating the folder and tables if they are missing."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: FastAPI may open the connection and use it on different threads.
    # Each request still gets its own connection, so this is safe.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.executescript(SCHEMA)
    return conn


# ---------- saving ----------

def save_executions(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Insert trades; a trade already saved (same exec_id) is skipped. Returns rows added."""
    before = conn.total_changes
    conn.executemany(
        """INSERT OR IGNORE INTO executions
           (exec_id, time, con_id, symbol, sec_type, currency, side, shares, price, commission, realized_pnl)
           VALUES (:exec_id, :time, :con_id, :symbol, :sec_type, :currency, :side, :shares, :price,
                   :commission, :realized_pnl)""",
        rows,
    )
    conn.commit()
    return conn.total_changes - before


def save_nav(conn: sqlite3.Connection, row: dict) -> None:
    """Save one day's account value; a later sync on the same day replaces it."""
    conn.execute(
        """INSERT OR REPLACE INTO nav_daily
           (date, net_liquidation, total_cash, gross_position_value, unrealized_pnl, realized_pnl, currency)
           VALUES (:date, :net_liquidation, :total_cash, :gross_position_value, :unrealized_pnl,
                   :realized_pnl, :currency)""",
        row,
    )
    conn.commit()


def save_cash_flow(conn: sqlite3.Connection, date: str, amount: float) -> None:
    """Record a deposit (+) or withdrawal (-) for a day."""
    conn.execute("INSERT OR REPLACE INTO cash_flows (date, amount) VALUES (?, ?)", (date, amount))
    conn.commit()


def save_positions(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executemany(
        """INSERT OR REPLACE INTO positions_daily
           (date, con_id, symbol, quantity, avg_cost, market_price, market_value, currency)
           VALUES (:date, :con_id, :symbol, :quantity, :avg_cost, :market_price, :market_value, :currency)""",
        rows,
    )
    conn.commit()


def save_prices(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executemany(
        """INSERT OR REPLACE INTO prices_daily (con_id, symbol, date, close)
           VALUES (:con_id, :symbol, :date, :close)""",
        rows,
    )
    conn.commit()


# ---------- loading ----------

def load_nav(conn: sqlite3.Connection) -> pd.Series:
    """Daily NAV indexed by date."""
    df = pd.read_sql("SELECT date, net_liquidation FROM nav_daily ORDER BY date", conn,
                     parse_dates=["date"], index_col="date")
    return df["net_liquidation"]


def load_cash_flows(conn: sqlite3.Connection) -> pd.Series:
    df = pd.read_sql("SELECT date, amount FROM cash_flows ORDER BY date", conn,
                     parse_dates=["date"], index_col="date")
    return df["amount"]


def load_executions(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM executions ORDER BY time", conn)


def load_positions(conn: sqlite3.Connection, date: str | None = None) -> pd.DataFrame:
    """Positions on a given date (default: the latest date saved)."""
    if date is None:
        date = conn.execute("SELECT MAX(date) FROM positions_daily").fetchone()[0]
    return pd.read_sql("SELECT * FROM positions_daily WHERE date = ?", conn, params=(date,))


def load_prices(conn: sqlite3.Connection, con_ids: list[int]) -> pd.DataFrame:
    """Adjusted closes, one column per symbol, indexed by date."""
    if not con_ids:
        return pd.DataFrame()
    marks = ",".join("?" * len(con_ids))
    df = pd.read_sql(f"SELECT symbol, date, close FROM prices_daily WHERE con_id IN ({marks})",
                     conn, params=list(con_ids), parse_dates=["date"])
    return df.pivot(index="date", columns="symbol", values="close").sort_index()
