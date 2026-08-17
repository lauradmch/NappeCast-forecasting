"""
Content of the Documentation / Predictions tab

"""


# --------------------------- LIBRARY --------------------------------
import pandas as pd
import numpy as np
import streamlit as st
import requests
import plotly.graph_objects as go
import logging
import os


from src.config import load_config
from requests.exceptions import RequestException
from src.models.prophet import (build_train_frame,
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

@st.cache_data(show_spinner=False)
def fetch_forecast(H: int):
    """
    Predict. Cached (@st.cache_data): only re-runs
    when `H` changes, not on every Streamlit rerun.
    Returns (last_train, forecast).
    """
    try:
        response = requests.post(f'{API_URL}/predict', params={'H': H}, timeout=60)
        response.raise_for_status()
    except RequestException as e:
        st.error(f"Could not reach the forecast API: {e}")
        return None
    data = response.json()
    forecast_df = pd.DataFrame(data["points"])
    forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
    last_train = pd.to_datetime(data["last_train"])
    return last_train, forecast_df


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
        with st.spinner("Fetching forecast from API..."):
            try:

                daily = build_daily(df_prediction)
                result = fetch_forecast(H)
                if result is None:
                    return
                last_train, forecast = result
                history, _ = build_train_frame(daily, H)

                fig = plot_forecast(history, forecast, H)
                st.plotly_chart(fig, use_container_width=True)

                # display loaded_at as a caption
                try:
                    info = requests.get(f"{API_URL}/model/info",
                                        params={"model": "Prophet", "horizon": H},
                                        timeout=5).json()
                    loaded_at = info.get("loaded_at")
                    if loaded_at:
                        # nicer display: "2026-08-17 14:32" instead of ISO
                        stamp = pd.to_datetime(loaded_at).strftime("%Y-%m-%d %H:%M")
                        st.caption(f"Model H={H} loaded at {stamp}")
                    else:
                        st.caption(f"Model H={H} not loaded yet")
                except requests.RequestException:
                    st.caption("Model status unavailable")

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
