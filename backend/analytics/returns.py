"""PnL and return calculations from daily NAV (net liquidation value).

Decisions (see README):
- PnL is IB's NAV change minus external cash flows (deposits +, withdrawals -).
- Time-weighted return (TWR) removes the effect of cash flows; it measures the investments.
- Money-weighted return (MWR) includes the timing of cash flows; it measures your money.
- Cash flows are assumed to arrive at the start of the day they are recorded on.
"""
import pandas as pd
from scipy.optimize import brentq


def _align_flows(nav: pd.Series, flows: pd.Series | None) -> pd.Series:
    """Cash flows on the same dates as NAV, 0 where there was none."""
    if flows is None or flows.empty:
        return pd.Series(0.0, index=nav.index)
    return flows.reindex(nav.index, fill_value=0.0).astype(float)


def daily_pnl(nav: pd.Series, flows: pd.Series | None = None) -> pd.Series:
    """Profit or loss each day: change in NAV minus money added that day.

    The first day has no previous value, so it is dropped.
    """
    return (nav.diff() - _align_flows(nav, flows)).iloc[1:]


def cumulative_pnl(nav: pd.Series, flows: pd.Series | None = None) -> pd.Series:
    """Running total of PnL since the first NAV date."""
    return daily_pnl(nav, flows).cumsum()


def twr_daily(nav: pd.Series, flows: pd.Series | None = None) -> pd.Series:
    """Daily time-weighted returns: NAV_t / (NAV_{t-1} + flow_t) - 1.

    The deposit arrives at the start of day t, so it is invested for the whole day
    and belongs in the starting value, not in the gain.
    """
    f = _align_flows(nav, flows)
    return (nav / (nav.shift(1) + f) - 1).iloc[1:]


def twr_cumulative(daily: pd.Series) -> pd.Series:
    """Chain-link daily returns: (1 + r1)(1 + r2)... - 1."""
    return (1 + daily).cumprod() - 1


def mwr(nav: pd.Series, flows: pd.Series | None = None, annualise: bool = False) -> float | None:
    """Money-weighted return (internal rate of return) over the whole NAV history.

    Cash flows from the investor's point of view: the starting NAV is paid in,
    each deposit is paid in, each withdrawal comes out, and the final NAV comes out.
    We find the daily rate g that makes their present value zero, then report
    (1 + g)^days - 1 for the period, or (1 + g)^365 - 1 if annualise is True.

    With no cash flows this equals the simple return NAV_end / NAV_start - 1.
    Returns None if there are fewer than two NAV points or no solution exists.
    """
    nav = nav.dropna().sort_index()
    if len(nav) < 2:
        return None
    start = nav.index[0]
    f = _align_flows(nav, flows).iloc[1:]  # a flow on the first day is already in NAV_0

    days = [0.0]
    amounts = [-float(nav.iloc[0])]
    for d, amt in f[f != 0].items():
        days.append(float((d - start).days))
        amounts.append(-float(amt))
    total_days = float((nav.index[-1] - start).days)
    days.append(total_days)
    amounts.append(float(nav.iloc[-1]))

    def npv(g: float) -> float:
        return sum(a / (1 + g) ** t for a, t in zip(amounts, days))

    try:
        g = brentq(npv, -0.99, 10.0)
    except ValueError:  # no sign change: no valid rate in range
        return None
    periods = 365.0 if annualise else total_days
    try:
        return (1 + g) ** periods - 1
    except OverflowError:
        return float("inf")
