#---------------------------------------------------------------------------------
# All useful shared functions for prophet
#---------------------------------------------------------------------------------


# ---------------------------- LIBRARY ---------------------------
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from src.config import load_config
from botocore.exceptions import ClientError

# ---------------------------- VARIABLES ---------------------------

CONFIG              = load_config()
DAILY_FEATURES      = CONFIG["model"]["prophet"]["data"]["features"]
TARGET              = CONFIG["model"]["prophet"]["data"]["target"]
HISTORY_DAYS        = 220 # Window of observed history shown on the chart (days)

# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
logger = logging.getLogger(__name__)

# ----------------------------  ---------------------------
# helper for shared extended & shifted features
def _extend_and_shift(daily: pd.DataFrame, H: int) -> tuple[pd.DataFrame, list[str]]:
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


    return df_all, regressor_cols

def build_train_frame(daily: pd.DataFrame, H: int) -> tuple[pd.DataFrame, list[str]]:
    """
    Builds the future-aware lagged regressors

    Parameters:
        daily : pd.DataFrame
            Historical daily-frequency data.
        H : int
            Forecast horizon, in days.
    
    Returns:
        df_prophet     : rows where y AND regressors are known (training)
        regressor_cols : names of the lagged columns
    """
    df_all, regressor_cols = _extend_and_shift(daily, H)

    return df_all.dropna(subset=["y"] + regressor_cols).reset_index(drop=True), regressor_cols


def build_daily(df_prediction: pd.DataFrame) -> pd.DataFrame:
    """
    Create the daily aggregation
    
    Parameters: 
        df_prediction : raw dataset

    Returns:
        datetime index, columns = TARGET + DAILY_FEATURES, mean per day.
    """
    d = df_prediction.copy()
    # Ensure a datetime index (the dataset has a date_index column)
    if not isinstance(d.index, pd.DatetimeIndex):
        if "date_index" in d.columns:
            d = d.set_index("date_index")
        d.index = pd.to_datetime(d.index)

    missing = set([TARGET] + DAILY_FEATURES) - set(d.columns)
    if missing:
        raise KeyError(f"Missing columns in df_prediction: {missing}")

    return d[[TARGET] + DAILY_FEATURES].groupby(level=0).mean()

def build_future_frame(daily: pd.DataFrame, H: int) -> tuple[pd.DataFrame, list[str]]:
    """
    Builds the future-aware lagged regressors for the forecasted period

    Parameters:
        daily : pd.DataFrame
            Historical daily-frequency data.
        H : int
            Forecast horizon, in days.
    
    Returns:
        future         : rows where regressors are known (history + H days)
            future.ds ⊇ df_prophet.ds ∪ [last_train+1 … last_train+H]

    """
    df_all, regressor_cols = _extend_and_shift(daily, H)

    return df_all.dropna(subset=regressor_cols).reset_index(drop=True), regressor_cols

# ---------------------------- PLOT ---------------------------

def plot_forecast(df_prophet: pd.DataFrame, forecast: pd.DataFrame, H: int) -> go.Figure:
    """
    Plotly version of fig2 (prophet_predict.py): recent observed history,
    +H day forecast and 80% uncertainty band.
    """
    last_train = df_prophet["ds"].max()
    fut = forecast[forecast["ds"] > last_train]
    min_date = pd.Timestamp("2026-01-01")
    hist = forecast[
        (forecast["ds"] <= last_train) &
        (forecast["ds"] >= min_date)
    ][["ds", "yhat"]]

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
        mode="markers", marker=dict(color="#b83333", size=4),
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
