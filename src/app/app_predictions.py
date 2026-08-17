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
from src.models.prophet import (build_train_frame,
                                build_future_frame,
                                build_daily,
                                plot_forecast)
from src.helper.spli import (forecast as spli_forecast,
                             category_label as spli_label)


# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- Forecast config (must stay identical to training to avoid
#     train/serve skew: same columns, same lag logic) ---------
TARGET = "niveau_nappe_eau"


# Silence the noisy Prophet/cmdstanpy logs in the Streamlit console
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


# ---------------------------- FORECAST HELPERS ---------------------------

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

    df_prophet, regressor_cols = build_train_frame(daily, H)
    future, regressor_cols = build_future_frame(daily, H)

    model = Prophet(**params)
    for col in regressor_cols:
        model.add_regressor(col)
    model.fit(df_prophet)

    forecast = model.predict(future)
    return df_prophet, forecast






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

                # TODO: ne faire que le predict (sans le fit)
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
                spli_rows = spli_forecast(daily[TARGET], forecast, last_train)
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
                        b_sev.metric("Severity", f"{label}")      
            except (KeyError, ValueError) as e:
                st.error(f"Could not compute the forecast: {e}")
