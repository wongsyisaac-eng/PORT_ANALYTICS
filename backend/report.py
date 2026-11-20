"""Print PnL, returns, risk and trade history from the local database.

Does not connect to IB. Run backend/sync.py first.
Usage:  python backend/report.py
"""
import pandas as pd

import storage
from analytics import returns, risk
from env_config import DB_PATH


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2%}"


def main() -> None:
    conn = storage.connect(DB_PATH)
    nav = storage.load_nav(conn)
    flows = storage.load_cash_flows(conn)
    trades = storage.load_executions(conn)
    positions = storage.load_positions(conn)
    prices = storage.load_prices(conn, positions["con_id"].tolist())
    conn.close()

    with pd.option_context("display.width", 140, "display.max_columns", 20,
                           "display.float_format", "{:,.4f}".format):
        section("Trading history")
        if trades.empty:
            print("No trades saved yet.")
        else:
            print(trades[["time", "symbol", "side", "shares", "price",
                          "commission", "realized_pnl"]].to_string(index=False))

        section("Daily NAV and PnL")
        if len(nav) < 2:
            print(f"{len(nav)} day(s) of NAV saved. PnL needs at least 2; run sync on another day.")
            if len(nav):
                print(nav.to_frame("nav").to_string())
        else:
            table = pd.DataFrame({
                "nav": nav,
                "daily_pnl": returns.daily_pnl(nav, flows),
                "cumulative_pnl": returns.cumulative_pnl(nav, flows),
                "twr_daily": returns.twr_daily(nav, flows),
            })
            table["twr_cumulative"] = returns.twr_cumulative(table["twr_daily"].dropna())
            print(table.to_string())

        section("Returns since first NAV date")
        if len(nav) >= 2:
            twr_total = returns.twr_cumulative(returns.twr_daily(nav, flows)).iloc[-1]
            print(f"Time-weighted:  {pct(twr_total)}")
            print(f"Money-weighted: {pct(returns.mwr(nav, flows))}")
        else:
            print("Needs at least 2 days of NAV.")

        section("Portfolio standard deviation")
        if positions.empty or nav.empty:
            print("No positions or NAV saved yet.")
        else:
            w = risk.weights(positions, nav.iloc[-1])
            print("Weights (share of NAV):")
            print(w.map("{:.2%}".format).to_string())
            rets = risk.price_returns(prices)
            if rets.empty:
                print("No price history saved; cannot compute ex-ante std.")
            else:
                d, a = risk.portfolio_std(w, rets)
                print(f"Ex-ante (from {len(rets)} days of prices, today's weights): "
                      f"daily {d:.2%}, annualised {a:.2%}")
                missing = sorted(set(w.index) - set(rets.columns))
                if missing:
                    print(f"  Left out (no prices): {', '.join(missing)}")
            realised = risk.realised_std(returns.twr_daily(nav, flows)) if len(nav) >= 2 else None
            print("Realised (from your NAV): " + (
                "not enough history yet (needs 20 days)" if realised is None
                else f"daily {realised[0]:.2%}, annualised {realised[1]:.2%}"))

        section("Correlation of holdings (daily returns)")
        if prices.shape[1] < 2:
            print("Needs price history for at least 2 holdings.")
        else:
            print(risk.correlation_matrix(risk.price_returns(prices)).round(2).to_string())


if __name__ == "__main__":
    main()
