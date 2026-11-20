import numpy as np
import pandas as pd
import pytest

from analytics import performance


def test_sharpe_by_hand():
    r = pd.Series([0.01, -0.01, 0.02, 0.0] * 5)
    s = performance.sharpe_ratio(r)
    assert s["daily"] == pytest.approx(r.mean() / r.std())
    assert s["annual"] == pytest.approx(r.mean() / r.std() * np.sqrt(252))


def test_sharpe_risk_free_lowers_ratio():
    r = pd.Series([0.01, -0.01, 0.02, 0.0] * 5)
    assert performance.sharpe_ratio(r, 0.05)["annual"] < performance.sharpe_ratio(r)["annual"]


def test_sharpe_none_when_short_or_flat():
    assert performance.sharpe_ratio(pd.Series([0.01, 0.02])) is None
    assert performance.sharpe_ratio(pd.Series([0.01] * 30)) is None
