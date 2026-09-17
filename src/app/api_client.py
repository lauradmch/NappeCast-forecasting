"""
HTTP client for the NappeCast API.
No Streamlit here: functions return Python objects or raise
requests.RequestException (network/HTTP errors) or KeyError (unexpected payload).
"""
import os

import pandas as pd
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _get(path: str, timeout: float, **params) -> dict:
    """GET {API_URL}{path}, raise on HTTP error, return the JSON body."""
    response = requests.get(f"{API_URL}{path}", params=params or None, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _post(path: str, timeout: float, **params) -> dict:
    """POST {API_URL}{path}, raise on HTTP error, return the JSON body."""
    response = requests.post(f"{API_URL}{path}", params=params or None, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_health() -> dict:
    return _get("/health", timeout=5)


def get_model_info(model: str, horizon: int) -> dict:
    return _get("/model/info", timeout=5, model=model, horizon=horizon)


def get_all_models_info() -> dict:
    return _get("/model/info/all", timeout=30)


def run_collect_pipeline() -> dict:
    """Collect new data and rebuild the datasets. Returns {"status", "stations", "processed_rows"}."""
    return _post("/pipeline/collect", timeout=120)


def post_predict(horizon: int) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Request a forecast. Returns (last_train, forecast_df with columns ds, yhat...)."""
    payload = _post("/predict", timeout=60, H=horizon)

    forecast_df = pd.DataFrame(payload["points"])
    forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
    last_train = pd.to_datetime(payload["last_train"])
    return last_train, forecast_df