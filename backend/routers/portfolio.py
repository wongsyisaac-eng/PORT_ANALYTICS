"""Read-only portfolio endpoints.

Every endpoint reads from the local SQLite database (filled by sync.py) and never
connects to IB, so the API works whether or not Gateway is open.
Each one stays thin: load data, call an analytics function, return JSON.
"""
import sqlite3
from collections.abc import Iterator

import pandas as pd
from fastapi import APIRouter, Depends

import storage
from analytics import performance, returns, risk
from env_config import DB_PATH, RISK_FREE_RATE
from serialize import df_records, num

router = APIRouter()


def get_conn() -> Iterator[sqlite3.Connection]:
    """One database connection per request, closed afterwards. Tests replace this."""
    conn = storage.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


Conn = Depends(get_conn)


@router.get("/positions")
def positions(conn: sqlite3.Connection = Conn) -> list[dict]:
    pos = storage.load_positions(conn)
    nav = storage.load_nav(conn)
    if pos.empty:
        return []
    pos["weight"] = pos["market_value"] / nav.iloc[-1] if not nav.empty else None
    cols = ["symbol", "quantity", "avg_cost", "market_price", "market_value", "currency", "weight"]
    return df_records(pos[cols])


@router.get("/trades")
def trades(conn: sqlite3.Connection = Conn) -> list[dict]:
    t = storage.load_executions(conn)
    cols = ["time", "symbol", "side", "shares", "price", "commission", "realized_pnl"]
    return df_records(t[cols])


@router.get("/nav")
def nav_history(conn: sqlite3.Connection = Conn) -> list[dict]:
    nav = storage.load_nav(conn)
    flows = storage.load_cash_flows(conn)
    twr = returns.twr_daily(nav, flows)
    table = pd.DataFrame({
        "nav": nav,
        "daily_pnl": returns.daily_pnl(nav, flows),
        "cumulative_pnl": returns.cumulative_pnl(nav, flows),
        "twr_daily": twr,
        "twr_cumulative": returns.twr_cumulative(twr),
    }, index=nav.index)
    return df_records(table.rename_axis("date").reset_index())


@router.get("/returns")
def total_returns(conn: sqlite3.Connection = Conn) -> dict:
    nav = storage.load_nav(conn)
    flows = storage.load_cash_flows(conn)
    enough = len(nav) >= 2
    return {
        "start_date": nav.index[0].date().isoformat() if len(nav) else None,
        "end_date": nav.index[-1].date().isoformat() if len(nav) else None,
        "days": len(nav),
        "twr_total": num(returns.twr_cumulative(returns.twr_daily(nav, flows)).iloc[-1]) if enough else None,
        "mwr": num(returns.mwr(nav, flows)) if enough else None,
    }


@router.get("/risk")
def portfolio_risk(conn: sqlite3.Connection = Conn) -> dict:
    nav = storage.load_nav(conn)
    flows = storage.load_cash_flows(conn)
    pos = storage.load_positions(conn)
    out = {"ex_ante_daily": None, "ex_ante_annual": None, "price_days": 0,
           "realised_daily": None, "realised_annual": None, "weights": []}
    if pos.empty or nav.empty:
        return out

    w = risk.weights(pos, nav.iloc[-1])
    out["weights"] = [{"symbol": s, "weight": num(v)} for s, v in w.items()]

    rets = risk.price_returns(storage.load_prices(conn, pos["con_id"].tolist()))
    if not rets.empty:
        try:
            daily, annual = risk.portfolio_std(w, rets)
            out.update(ex_ante_daily=num(daily), ex_ante_annual=num(annual), price_days=len(rets))
        except ValueError:  # no price history for any holding
            pass

    realised = risk.realised_std(returns.twr_daily(nav, flows)) if len(nav) >= 2 else None
    if realised:
        out.update(realised_daily=num(realised[0]), realised_annual=num(realised[1]))
    return out


@router.get("/sharpe")
def sharpe(conn: sqlite3.Connection = Conn) -> dict:
    nav = storage.load_nav(conn)
    flows = storage.load_cash_flows(conn)
    daily = returns.twr_daily(nav, flows) if len(nav) >= 2 else pd.Series(dtype=float)
    result = performance.sharpe_ratio(daily, RISK_FREE_RATE)
    return {
        "annual": num(result["annual"]) if result else None,
        "daily": num(result["daily"]) if result else None,
        "risk_free_annual": RISK_FREE_RATE,
        "observations": len(daily),
        "min_observations": 20,
    }


@router.get("/correlation")
def correlation(conn: sqlite3.Connection = Conn) -> dict:
    pos = storage.load_positions(conn)
    prices = storage.load_prices(conn, pos["con_id"].tolist())
    if prices.shape[1] < 2:
        return {"symbols": [], "matrix": []}
    corr = risk.correlation_matrix(risk.price_returns(prices))
    return {
        "symbols": list(corr.columns),
        "matrix": [[num(v) for v in row] for row in corr.to_numpy()],
    }
