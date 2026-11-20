"""Risk-adjusted performance: Sharpe ratio.

Decisions (see README):
- Sharpe = mean(daily return - daily risk-free rate) / std(daily return) * sqrt(252).
- Returns are the daily time-weighted returns from NAV (cash flows removed).
- The annual risk-free rate (RISK_FREE_RATE in .env, default 0) is converted to a
  daily rate by compounding over 252 trading days.
- Needs at least min_obs daily returns, otherwise the ratio is not meaningful.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sharpe_ratio(daily_returns: pd.Series, risk_free_annual: float = 0.0,
                 min_obs: int = 20, periods: int = TRADING_DAYS) -> dict | None:
    """Sharpe ratio of a daily return series.

    Returns {"daily", "annual", "mean_excess_daily"} or None if there are fewer than
    min_obs returns or the returns have zero volatility.
    """
    r = daily_returns.dropna()
    if len(r) < max(min_obs, 2):
        return None
    rf_daily = (1 + risk_free_annual) ** (1 / periods) - 1
    excess = r - rf_daily
    std = float(r.std())
    if not np.isfinite(std) or std < 1e-12:
        return None
    daily = float(excess.mean()) / std
    return {"daily": daily, "annual": daily * np.sqrt(periods),
            "mean_excess_daily": float(excess.mean())}
