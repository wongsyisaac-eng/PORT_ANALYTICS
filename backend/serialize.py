"""Turn pandas results into plain JSON-safe Python values.

JSON has no NaN or infinity, so those become None (null). Dates become ISO strings.
"""
import math
from datetime import date, datetime

import numpy as np
import pandas as pd


def clean(v):
    """One value -> something json.dumps accepts."""
    if v is None:
        return None
    if isinstance(v, np.generic):  # numpy number -> plain Python number
        v = v.item()
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if v is pd.NaT:
        return None
    if isinstance(v, datetime):  # includes pd.Timestamp
        midnight = v.hour == v.minute == v.second == v.microsecond == 0
        return v.date().isoformat() if midnight else v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return v


def num(x) -> float | None:
    """A number as float, or None if missing or not finite."""
    return None if x is None else clean(float(x))


def df_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list of row dicts with clean values."""
    return [{k: clean(v) for k, v in row.items()} for row in df.to_dict("records")]
