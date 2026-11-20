"""Synthetic price cases that can be checked by hand."""
import numpy as np
import pandas as pd
import pytest

from analytics import risk

DATES = pd.date_range("2026-01-01", periods=3, freq="D")


def test_correlation_plus_and_minus_one():
    a = pd.Series([0.01, -0.02, 0.03, -0.01])
    rets = pd.DataFrame({"A": a, "B": 2 * a, "C": -a})
    corr = risk.correlation_matrix(rets)
    assert corr.loc["A", "B"] == pytest.approx(1.0)
    assert corr.loc["A", "C"] == pytest.approx(-1.0)


def test_price_returns():
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0]}, index=DATES)
    assert risk.price_returns(prices)["A"].tolist() == pytest.approx([0.10, -0.10])


def test_weights_share_of_nav():
    pos = pd.DataFrame({"symbol": ["A", "B"], "market_value": [600.0, -200.0]})
    w = risk.weights(pos, nav=1000.0)
    assert w["A"] == pytest.approx(0.6)
    assert w["B"] == pytest.approx(-0.2)  # short position


def test_half_weight_halves_std():
    rets = pd.DataFrame({"A": [0.01, -0.02, 0.03, -0.01]})
    daily, annual = risk.portfolio_std(pd.Series({"A": 0.5}), rets)
    assert daily == pytest.approx(0.5 * rets["A"].std())
    assert annual == pytest.approx(daily * np.sqrt(252))


def test_perfect_hedge_has_zero_std():
    a = pd.Series([0.01, -0.02, 0.03, -0.01])
    rets = pd.DataFrame({"A": a, "B": a})
    daily, _ = risk.portfolio_std(pd.Series({"A": 0.5, "B": -0.5}), rets)
    assert daily == pytest.approx(0.0, abs=1e-12)


def test_realised_std_needs_enough_history():
    assert risk.realised_std(pd.Series([0.01] * 5)) is None
    assert risk.realised_std(pd.Series([0.01, -0.01] * 10)) is not None
