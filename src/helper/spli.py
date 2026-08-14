#---------------------------------------------------------------------------------
# All useful shared functions for data
#---------------------------------------------------------------------------------


# ---------------------------- LIBRARY ---------------------------
import pandas as pd
import numpy as np
import logging

from scipy.stats import norm

from src.config import load_config

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

MIN_FORECAST_DAYS = 14   # forecast-only months need MORE than this many days in forecast_spli

# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
logger = logging.getLogger(__name__)


# ---------------------------- SPLI ON THE FORECAST ---------------------------
# SPLI recipe (identical to standardize_index() in extreme_events_analysis.ipynb):
#   monthly mean of the groundwater level -> group by calendar month ->
#   Gringorten plotting position (rank - 0.44)/(n + 1 - 0.88) -> norm.ppf.
# We standardize each forecast month against the SAME calendar month in history,
# so the value is comparable to the SPLI column used in app_stats.py.

# Drought / wetness thresholds (same as app_stats.py: moderate -1, severe -1.5, extreme -2)
def category_label(v: float)-> tuple[str, str]:
    """Return (category, color) for an SPLI value."""
    if v <= -2.0:  return "Extreme drought",  "#67001f"
    if v <= -1.5:  return "Severe drought",   "#b2182b"
    if v <= -1.0:  return "Moderate drought", "#ef8a62"
    if v <  1.0:   return "Normal",           "#4d4d4d"
    if v <  1.5:   return "Moderately wet",   "#67a9cf"
    if v <  2.0:   return "Very wet",         "#2166ac"
    
    return "Extremely wet", "#053061"


def gringorten_zscore(pool_values: np.ndarray, value: float) -> float:
    """
    Normal-scores position of `value` within (pool_values + value), using the
    Gringorten plotting position. This is exactly what standardize_index does
    for one member of a calendar-month group: average rank, count including the
    new value, then inverse normal.
    """
    vals = np.append(np.asarray(pool_values, dtype=float), value)
    rank_v = pd.Series(vals).rank().iloc[-1]      # average rank (1-based) of `value`
    n = len(vals)
    p = (rank_v - 0.44) / (n + 1 - 2 * 0.44)      # Gringorten

    return float(norm.ppf(p))


def forecast(daily_target: pd.Series, forecast: pd.DataFrame, last_train) -> list:
    """
    SPLI of the forecast, one value per calendar month the forecast touches.

    Month-mean rule:
      * Transition month (has observed AND forecast days): complete the month
        with observed + forecast days -> whole-month mean ("blended").
      * Forecast-only month: use forecast days only, and include it ONLY if it
        has MORE than MIN_FORECAST_DAYS (=14) forecast days.

    Each month is standardized against the SAME calendar month in prior years
    (the current year's month is excluded from the reference pool), using the
    Gringorten normal-scores recipe identical to standardize_index().

    daily_target : observed daily groundwater level (historical reference)
    forecast     : Prophet output (columns ds, yhat)
    last_train   : last observed date (forecast = rows after it)

    Returns dicts: {month, spli, mean_level, obs_days, fc_days, days_in_month, mode}.
    """
    obs = daily_target.dropna()                                 # observed daily GWL
    fut = forecast[forecast["ds"] > last_train].set_index("ds")["yhat"]
    combined = pd.concat([obs, fut])                            # observed + forecast, no overlap
    hist_monthly = obs.resample("MS").mean()                   # historical reference

    out = []
    for month in fut.resample("MS").mean().dropna().index:
        in_month = lambda idx: (idx.year == month.year) & (idx.month == month.month)
        obs_days = int(obs.index[in_month(obs.index)].size)
        fc_days = int(fut.index[in_month(fut.index)].size)

        if obs_days > 0:                                        # transition month -> whole month
            mean_level = float(combined[in_month(combined.index)].mean())
            mode = "blended"
        else:                                                  # forecast-only month
            if fc_days <= MIN_FORECAST_DAYS:                   # not enough forecast days -> skip
                continue
            mean_level = float(fut[in_month(fut.index)].mean())
            mode = "forecast-only"

        # reference pool: same calendar month, prior years only (exclude current month)
        pool = hist_monthly[(hist_monthly.index.month == month.month)
                            & (hist_monthly.index != month)].dropna().values
        out.append({
            "month": month,
            "spli": gringorten_zscore(pool, mean_level),
            "mean_level": mean_level,
            "obs_days": obs_days,
            "fc_days": fc_days,
            "days_in_month": int(month.days_in_month),
            "mode": mode,
        })

    return out

