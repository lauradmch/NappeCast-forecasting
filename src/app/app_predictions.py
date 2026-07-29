"""
Content of the Documentation / Predictions tab

"""


# --------------------------- LIBRARY --------------------------------
import ast
import pandas as pd
import numpy as np
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import logging
import os
import yaml

from scipy.stats import norm
from prophet import Prophet

from src.config import load_config

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- Forecast config (must stay identical to training to avoid
#     train/serve skew: same columns, same lag logic) ---------
TARGET = "niveau_nappe_eau"
DAILY_FEATURES = [
    "shortwave_radiation_sum", "et0_fao_evapotranspiration",
    "soil_temperature_0_to_100cm_mean",
    "P_cum_90d", "Peff_cum_90d",
    "Temperature_mean_90d",
]

# Window of observed history shown on the chart (days)
HISTORY_DAYS = 220

# Silence the noisy Prophet/cmdstanpy logs in the Streamlit console
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


# ---------------------------- FORECAST HELPERS ---------------------------

def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduces the daily aggregation from prophet_predict.py.
    Input: raw dataset (df_prediction). Output: datetime index,
    columns = TARGET + DAILY_FEATURES, mean per day.
    """
    d = df.copy()
    # Ensure a datetime index (the dataset has a date_index column)
    if not isinstance(d.index, pd.DatetimeIndex):
        if "date_index" in d.columns:
            d = d.set_index("date_index")
        d.index = pd.to_datetime(d.index)

    missing = set([TARGET] + DAILY_FEATURES) - set(d.columns)
    if missing:
        raise KeyError(f"Missing columns in df_prediction: {missing}")

    return d[[TARGET] + DAILY_FEATURES].groupby(level=0).mean()


def build_frames(daily: pd.DataFrame, H: int):
    """
    Builds the future-aware lagged regressors (identical to lines
    85-103 of prophet_predict.py, but with H parameterized).

    Returns:
        df_prophet     : rows where y AND regressors are known (training)
        future         : rows where regressors are known (history + H days)
        regressor_cols : names of the lagged columns
    """
    # Extend the index by H days to create the forecast rows
    future_idx = pd.date_range(daily.index.min(), periods=len(daily) + H, freq="D")
    df_ext = daily.reindex(future_idx)

    # Shift each feature forward by H days:
    # the value observed H days ago becomes a known regressor for the future
    for col in DAILY_FEATURES:
        df_ext[f"{col}_lag{H}"] = df_ext[col].shift(H)
    regressor_cols = [f"{col}_lag{H}" for col in DAILY_FEATURES]

    df_all = pd.DataFrame({"ds": df_ext.index, "y": df_ext[TARGET].values})
    for col in regressor_cols:
        df_all[col] = df_ext[col].values

    df_prophet = df_all.dropna(subset=["y"] + regressor_cols).reset_index(drop=True)
    future = df_all[["ds"] + regressor_cols].dropna(subset=regressor_cols).reset_index(drop=True)
    return df_prophet, future, regressor_cols


# Per-horizon Prophet hyperparameters. Each allowed H has its own config,
# so H=14 and H=30 can be tuned independently. Baseline values are identical;
# adjust each block (e.g. changepoint_prior_scale) as you validate each horizon.
HYPERPARAMS = {
    14: {
        "seasonality_mode": "additive",
        "weekly_seasonality": False,
        "daily_seasonality": False,
        "yearly_seasonality": True,
        "interval_width": 0.80,          # -> 80% interval
        "changepoint_prior_scale": 0.1,
        "seasonality_prior_scale": 0.1,
        "changepoint_range": 0.8,
    },
    30: {
        "seasonality_mode": "additive",
        "weekly_seasonality": False,
        "daily_seasonality": False,
        "yearly_seasonality": True,
        "interval_width": 0.80,          # -> 80% interval
        "changepoint_prior_scale": 0.3,
        "seasonality_prior_scale": 10,
        "changepoint_range": 0.8,
    },
}


@st.cache_data(show_spinner=False)
def fit_and_forecast(daily: pd.DataFrame, H: int):
    """
    Retrains Prophet and predicts. Cached (@st.cache_data): only re-runs
    when `daily` or `H` change — not on every Streamlit rerun.
    Uses the hyperparameter config bound to this H (HYPERPARAMS[H]).
    Returns (df_prophet, forecast).
    """
    params = HYPERPARAMS[H]

    df_prophet, future, regressor_cols = build_frames(daily, H)

    model = Prophet(**params)
    for col in regressor_cols:
        model.add_regressor(col)
    model.fit(df_prophet)

    forecast = model.predict(future)
    return df_prophet, forecast


def plot_forecast(df_prophet: pd.DataFrame, forecast: pd.DataFrame, H: int) -> go.Figure:
    """
    Plotly version of fig2 (prophet_predict.py): recent observed history,
    +H day forecast and 80% uncertainty band.
    """
    last_train = df_prophet["ds"].max()
    fut = forecast[forecast["ds"] > last_train]
    hist = forecast[forecast["ds"] <= last_train]

    # Recent observed history only
    recent_cut = last_train - pd.Timedelta(days=HISTORY_DAYS)
    obs = df_prophet[df_prophet["ds"] >= recent_cut]

    fig = go.Figure()

    # --- Uncertainty band: upper bound (invisible) then filled lower bound
    fig.add_trace(go.Scatter(
        x=fut["ds"], y=fut["yhat_upper"],
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fut["ds"], y=fut["yhat_lower"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(214,39,40,0.18)",
        name="80% interval",
    ))

    # --- Forecast (+H days)
    fig.add_trace(go.Scatter(
        x=fut["ds"], y=fut["yhat"],
        mode="lines", line=dict(color="#d62728", width=3),
        name=f"Forecast (+{H}d)",
    ))

    # --- Recent observed (ground truth)
    fig.add_trace(go.Scatter(
        x=obs["ds"], y=obs["y"],
        mode="markers", marker=dict(color="#0f5792", size=5),
        name="Observed",
    ))
    # --- Prediction on history
    fig.add_trace(go.Scatter(
        x=hist["ds"], y=hist["yhat"],
        mode="markers", marker=dict(color="#d6272789", size=5),
        name=f"Prediction",
    ))

    # --- Vertical line = last training date
    fig.add_vline(x=last_train, line_dash="dash", line_color="gray")

    fig.update_layout(
        title=f"Groundwater level — Prophet forecast (H={H} days)",
        xaxis_title="Date", yaxis_title="Groundwater level (m)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=60),
    )
    return fig


# ---------------------------- SPLI ON THE FORECAST ---------------------------
#
# SPLI recipe (identical to standardize_index() in extreme_events_analysis.ipynb):
#   monthly mean of the groundwater level -> group by calendar month ->
#   Gringorten plotting position (rank - 0.44)/(n + 1 - 0.88) -> norm.ppf.
# We standardize each forecast month against the SAME calendar month in history,
# so the value is comparable to the SPLI column used in app_stats.py.

# Drought / wetness thresholds (same as app_stats.py: moderate -1, severe -1.5, extreme -2)
def spli_label(v: float):
    """Return (category, color) for an SPLI value."""
    if v <= -2.0:  return "Extreme drought",  "#67001f"
    if v <= -1.5:  return "Severe drought",   "#b2182b"
    if v <= -1.0:  return "Moderate drought", "#ef8a62"
    if v <  1.0:   return "Normal",           "#4d4d4d"
    if v <  1.5:   return "Moderately wet",   "#67a9cf"
    if v <  2.0:   return "Very wet",         "#2166ac"
    return "Extremely wet", "#053061"


def _gringorten_zscore(pool_values: np.ndarray, value: float) -> float:
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


MIN_FORECAST_DAYS = 14   # forecast-only months need MORE than this many days

def forecast_spli(daily_target: pd.Series, forecast: pd.DataFrame, last_train) -> list:
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
    hist = forecast[forecast["ds"] <= last_train].set_index("ds")["yhat"]
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
            "spli": _gringorten_zscore(pool, mean_level),
            "mean_level": mean_level,
            "obs_days": obs_days,
            "fc_days": fc_days,
            "days_in_month": int(month.days_in_month),
            "mode": mode,
        })
    return out


# ---------------------------- METHODS ---------------------------

def render_predictions(df_prediction: pd.DataFrame) -> None:

    # ============ Prophet forecast (computed in the app) ============
    st.subheader("Groundwater level forecast (Prophet)")

    H = st.radio(
        "Forecast horizon (days)",
        options=[14, 30],
        index=1,
        horizontal=True,
        help="H sets the regressor lag, the horizon, and its own hyperparameter config.",
    )
    run = st.button("Run forecast")

    # auto-run once on first load with default params
    if run or not st.session_state.get("forecast_ran", False):
        st.session_state["forecast_ran"] = True
        with st.spinner("Training + Prophet forecast in progress..."):
            try:
                daily = build_daily(df_prediction)
                df_prophet, forecast = fit_and_forecast(daily, H)
                fig = plot_forecast(df_prophet, forecast, H)
                st.plotly_chart(fig, use_container_width=True)

                last_train = df_prophet["ds"].max()

                # ---- SPLI of the forecast period ----
                st.markdown("**Forecast SPLI (Standardised Piezometric Level Index)**")
                st.caption(
                    "Each forecast month standardised against the same calendar month "
                    "in prior years. Transition months are completed with observed + "
                    "forecast days; forecast-only months need > 14 forecast days."
                )
                spli_rows = forecast_spli(daily[TARGET], forecast, last_train)
                if not spli_rows:
                    st.info(
                        "No forecast month qualifies for an SPLI "
                        "(forecast-only months need more than 14 days)."
                    )
                else:
                    for r in spli_rows:
                        label, color = spli_label(r["spli"])
                        b_month, b_spli, b_sev = st.columns(3)
                        # Month box
                        b_month.metric("Month", r["month"].strftime("%B %Y"))
                        # SPLI value box (same st.metric look as app_stats)
                        b_spli.metric("SPLI", f"{r['spli']:+.2f}")
                        # Severity box: name + colour
                        b_sev.markdown(
                            f"<div style='border:1px solid {color};border-radius:10px;"
                            f"padding:0.4rem 1rem;background:{color}1a;'>"
                            f"<div style='color:grey;font-size:0.8rem'>Severity</div>"
                            f"<div style='color:{color};font-weight:700;font-size:1.25rem'>"
                            f"{label}</div></div>",
                            unsafe_allow_html=True,
                        )
            except (KeyError, ValueError) as e:
                st.error(f"Could not compute the forecast: {e}")
