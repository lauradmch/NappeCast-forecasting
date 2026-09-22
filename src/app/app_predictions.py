"""
Content of the Documentation / Predictions tab

"""


# --------------------------- LIBRARY --------------------------------
import logging
import os

import pandas as pd
import requests
import streamlit as st

from src.app import api_client
from src.config import load_config
from src.helper.constants import MIN_FORECAST_DAYS, TARGET_COL
from src.helper.spli import category_label as spli_label
from src.helper.spli import forecast as spli_forecast
from src.models.prophet import build_daily, build_train_frame, plot_forecast
from datetime import date
from typing import Optional, Literal

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- Forecast config (must stay identical to training to avoid
#     train/serve skew: same columns, same lag logic) ---------


# Silence the noisy Prophet/cmdstanpy logs in the Streamlit console
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


# ---------------------------- FORECAST HELPERS ---------------------------


@st.cache_data(show_spinner=False)
def fetch_forecast(code_bss: str, horizon: Literal[14, 30], start_date: date):
    return api_client.post_forecast(code_bss, horizon, start_date)


def _render_model_status(H: int) -> None:
    """Caption with the time the model for horizon H was loaded."""
    try:
        info = api_client.get_model_info("Prophet", H)
    except requests.RequestException:
        st.caption("Model status unavailable")
        return
    loaded_at = info.get("loaded_at")
    if loaded_at:
        stamp = pd.to_datetime(loaded_at).strftime("%Y-%m-%d %H:%M")
        st.caption(f"Model H={H} loaded at {stamp}")
    else:
        st.caption(f"Model H={H} not loaded yet")


def _render_spli(daily: pd.DataFrame, forecast: pd.DataFrame, last_train: pd.Timestamp) -> None:
    """SPLI of the forecast period, one row of metrics per month."""
    st.markdown("**Forecast SPLI (Standardised Piezometric Level Index)**")
    st.caption(
        "Each forecast month standardised against the same calendar month "
        "in prior years. Transition months are completed with observed + "
        f"forecast days; forecast-only months need > {MIN_FORECAST_DAYS} forecast days."
    )
    spli_rows = spli_forecast(daily[TARGET_COL], forecast, last_train)
    if not spli_rows:
        st.info(
            "No forecast month qualifies for an SPLI "
            f"(forecast-only months need more than {MIN_FORECAST_DAYS} days)."
        )
        return
    for r in spli_rows:
        label, _ = spli_label(r["spli"])
        b_month, b_spli, b_sev = st.columns(3)
        b_month.metric("Month", r["month"].strftime("%B %Y"))
        b_spli.metric("SPLI", f"{r['spli']:+.2f}")
        b_sev.metric("Severity", label)


# ---------------------------- METHODS ---------------------------

def render_predictions(code_bss: str, start_date: date, df_prediction: pd.DataFrame) -> None:
    # ============ Prophet forecast (computed in the app) ============
    st.subheader("Groundwater level forecast (Prophet)")

    horizon = st.radio(
        "Forecast horizon (days)",
        options=[14, 30],
        index=1,
        horizontal=True,
        help="H sets the regressor lag, the horizon, and its own hyperparameter config.",
    )

    with st.spinner("Fetching forecast from API..."):
        try:
            last_train, forecast = fetch_forecast(code_bss, horizon, start_date)
 
        except (requests.RequestException, KeyError) as e:
            st.error(f"Could not reach the forecast API: {e}")
            return

    try:
        daily = build_daily(df_prediction)
        history, _ = build_train_frame(daily, horizon)
        st.plotly_chart(plot_forecast(history, forecast, horizon), use_container_width=True)
        _render_model_status(horizon)
        _render_spli(daily, forecast, last_train)

    except (KeyError, ValueError) as e:
        st.error(f"Could not compute the forecast: {e}")