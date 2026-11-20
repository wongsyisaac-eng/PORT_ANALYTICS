"""Risk measures: correlation of holdings and portfolio standard deviation.

Decisions (see README):
- Ex-ante std uses about a year of daily adjusted closes of the holdings,
  weighted by today's market values as a share of NAV. Cash is the remainder
  and is treated as having zero volatility. Short positions get negative weights.
- Prices are in each stock's own currency; FX moves are ignored.
- Annualisation assumes 252 trading days.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def price_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily simple returns, one column per symbol. Days missing any price are dropped."""
    return prices.sort_index().pct_change(fill_method=None).dropna(how="any")


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation of daily returns between every pair of holdings."""
    return returns.corr()


def weights(positions: pd.DataFrame, nav: float) -> pd.Series:
    """Each holding's market value as a fraction of NAV, indexed by symbol."""
    w = positions.groupby("symbol")["market_value"].sum() / nav
    w.name = "weight"
    return w


def portfolio_std(w: pd.Series, returns: pd.DataFrame,
                periods: int = TRADING_DAYS) -> tuple[float, float]:
    """Standard deviation of the portfolio: sqrt(w' * Cov * w).

    Only symbols present in both w and returns are used.
    Returns (daily std, annualised std).
    """
    cols = [s for s in w.index if s in returns.columns]
    if not cols:
        raise ValueError("No price history for any holding.")
    cov = returns[cols].cov().to_numpy()
    wv = w[cols].to_numpy()
    daily = float(np.sqrt(wv @ cov @ wv))
    return daily, daily * np.sqrt(periods)


def realised_std(nav_returns: pd.Series, min_obs: int = 20,
                 periods: int = TRADING_DAYS) -> tuple[float, float] | None:
    """Std of the account's own daily returns, or None if history is too short."""
    r = nav_returns.dropna()
    if len(r) < min_obs:
        return None
    daily = float(r.std())
    return daily, daily * np.sqrt(periods)
