"""Pull data from IB (read-only) and save it to SQLite.

Run once a day with TWS or IB Gateway open:  python backend/sync.py
Each run saves new trades, today's NAV and positions, and ~1 year of daily prices
for every stock held. Running it twice is safe: nothing is duplicated.
"""
import sys
from datetime import date

from ib_async import IB, Contract

import storage
from env_config import IB_HOST, IB_PORT, IB_CLIENT_ID, DB_PATH

# IB uses the largest float to mean "no value" (e.g. realised PnL on an opening trade)
UNSET = sys.float_info.max
NAV_TAGS = {
    "NetLiquidation": "net_liquidation",
    "TotalCashValue": "total_cash",
    "GrossPositionValue": "gross_position_value",
    "UnrealizedPnL": "unrealized_pnl",
    "RealizedPnL": "realized_pnl",
}


def clean(x: float | None) -> float | None:
    return None if x is None or x == UNSET else x


def fetch_executions(ib: IB) -> list[dict]:
    rows = []
    for fill in ib.reqExecutions():
        ex, cr = fill.execution, fill.commissionReport
        has_report = bool(cr and cr.execId)
        rows.append({
            "exec_id": ex.execId,
            "time": ex.time.isoformat(),
            "con_id": fill.contract.conId,
            "symbol": fill.contract.symbol,
            "sec_type": fill.contract.secType,
            "currency": fill.contract.currency,
            "side": ex.side,
            "shares": ex.shares,
            "price": ex.price,
            "commission": clean(cr.commission) if has_report else None,
            "realized_pnl": clean(cr.realizedPNL) if has_report else None,
        })
    return rows


def fetch_nav(ib: IB, account: str, today: str) -> dict:
    row = {"date": today, "currency": None, **{col: None for col in NAV_TAGS.values()}}
    for v in ib.accountSummary(account):
        # Each tag is also reported per currency; the base-currency line is the one we want.
        if v.tag in NAV_TAGS and v.currency not in ("", "BASE") and row["currency"] in (None, v.currency):
            row[NAV_TAGS[v.tag]] = float(v.value)
            row["currency"] = v.currency
    return row


def fetch_positions(ib: IB, account: str, today: str) -> list[dict]:
    return [{
        "date": today,
        "con_id": p.contract.conId,
        "symbol": p.contract.symbol,
        "quantity": p.position,
        "avg_cost": p.averageCost,
        "market_price": p.marketPrice,
        "market_value": p.marketValue,
        "currency": p.contract.currency,
        "sec_type": p.contract.secType,  # used below, not stored
    } for p in ib.portfolio(account) if p.position != 0]


def fetch_prices(ib: IB, con_id: int, symbol: str) -> list[dict]:
    contract = Contract(conId=con_id)
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr="1 Y", barSizeSetting="1 day",
        whatToShow="ADJUSTED_LAST", useRTH=True,
    )
    return [{"con_id": con_id, "symbol": symbol, "date": str(b.date), "close": b.close} for b in bars]


def main() -> None:
    today = date.today().isoformat()
    conn = storage.connect(DB_PATH)
    ib = IB()
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, readonly=True)
    try:
        account = ib.managedAccounts()[0]

        added = storage.save_executions(conn, fetch_executions(ib))
        print(f"Trades: {added} new")

        storage.save_nav(conn, fetch_nav(ib, account, today))
        print(f"NAV: saved for {today}")

        positions = fetch_positions(ib, account, today)
        storage.save_positions(conn, positions)
        print(f"Positions: {len(positions)}")

        for p in positions:
            if p["sec_type"] != "STK":  # stocks and ETFs only for now
                print(f"Prices {p['symbol']}: skipped ({p['sec_type']})")
                continue
            bars = fetch_prices(ib, p["con_id"], p["symbol"])
            if bars:
                storage.save_prices(conn, bars)
                print(f"Prices {p['symbol']}: {len(bars)} days")
            else:
                print(f"Prices {p['symbol']}: none returned (check market data permissions)")
            ib.sleep(1)  # stay within IB's pacing limits
    finally:
        ib.disconnect()
        conn.close()


if __name__ == "__main__":
    main()
