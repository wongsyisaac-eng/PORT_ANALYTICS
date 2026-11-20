"""Synthetic NAV cases that can be checked by hand."""
import pandas as pd
import pytest

from analytics import returns

DATES = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])


def test_pnl_and_twr_without_flows():
    nav = pd.Series([100.0, 110.0, 99.0], index=DATES)
    assert returns.daily_pnl(nav).tolist() == pytest.approx([10.0, -11.0])
    assert returns.cumulative_pnl(nav).tolist() == pytest.approx([10.0, -1.0])
    daily = returns.twr_daily(nav)
    assert daily.tolist() == pytest.approx([0.10, -0.10])
    assert returns.twr_cumulative(daily).iloc[-1] == pytest.approx(-0.01)  # 1.1 * 0.9 - 1


def test_deposit_is_not_profit():
    # NAV jumps 100 -> 150 only because 50 was deposited: no PnL, no return.
    nav = pd.Series([100.0, 150.0, 165.0], index=DATES)
    flows = pd.Series([50.0], index=DATES[1:2])
    assert returns.daily_pnl(nav, flows).tolist() == pytest.approx([0.0, 15.0])
    assert returns.twr_daily(nav, flows).tolist() == pytest.approx([0.0, 0.10])


def test_mwr_without_flows_is_simple_return():
    nav = pd.Series([100.0, 105.0, 110.0], index=DATES)
    assert returns.mwr(nav) == pytest.approx(0.10)


def test_mwr_weights_money_by_timing():
    # Lose 50% on 100, then deposit 1000 and gain 10%: TWR is -45%,
    # but most of the money earned +10%, so MWR is positive.
    nav = pd.Series([100.0, 50.0, 1155.0], index=DATES)
    flows = pd.Series([1000.0], index=DATES[2:3])
    twr = returns.twr_cumulative(returns.twr_daily(nav, flows)).iloc[-1]
    assert twr == pytest.approx(-0.45)
    assert returns.mwr(nav, flows) > 0


def test_mwr_needs_two_points():
    assert returns.mwr(pd.Series([100.0], index=DATES[:1])) is None
