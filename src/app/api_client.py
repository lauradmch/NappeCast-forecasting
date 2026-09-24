"""
HTTP client for the NappeCast API.
No Streamlit here: functions return Python objects or raise
requests.RequestException (network/HTTP errors) or KeyError (unexpected payload).
"""
import os
import pandas as pd
import requests

from datetime import date
from typing import Literal

API_URL = os.getenv("API_URL", "http://localhost:8000")
PIPELINE_SECRET = os.getenv("PIPELINE_SECRET")

def _get(path: str, timeout: float, headers: dict | None = None, **params) -> dict:
    """GET {API_URL}{path}, raise on HTTP error, return the JSON body."""
    response = requests.get(f"{API_URL}{path}", params=params or None,
                             headers=headers, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise requests.exceptions.HTTPError(f"{e} — detail: {detail}", response=response) from e
    return response.json()


def _post(path: str, timeout: float, headers: dict | None = None, **params) -> dict:
    """POST {API_URL}{path}, raise on HTTP error, return the JSON body."""
    response = requests.post(f"{API_URL}{path}", params=params or None,
                             headers=headers, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise requests.exceptions.HTTPError(f"{e} — detail: {detail}", response=response) from e
    return response.json()


def get_health() -> dict:
    return _get("/health", timeout=5)


def get_model_info(model: str, horizon: int) -> dict:
    return _get("/model/info", timeout=5, model=model, horizon=horizon)


def _secret_headers() -> dict:
    """Auth header for protected endpoints (/pipeline/collect, /train)."""
    if not PIPELINE_SECRET:
        raise RuntimeError("PIPELINE_SECRET is not set in the app environment.")
    return {"X-Pipeline-Secret": PIPELINE_SECRET}


def run_collect_pipeline() -> dict:
    """Collect new data and rebuild the datasets. Returns InterimResponse"""
    return _post("/pipeline/collect", timeout=120, headers=_secret_headers())


def run_feat_pipeline() -> dict:
    """Collect feature ingineering. Returns ProcessedResponse"""
    return _post("/pipeline/feat", timeout=120, headers=_secret_headers())


def post_station(code_bss: str) -> pd.DataFrame:
    """Request a station. Returns the station data as a DataFrame."""
    payload = _post("/data/station", timeout=60, code_bss=code_bss, headers=_secret_headers())

    if payload.get("status") != "ok" or "data" not in payload:
        raise RuntimeError(f"Erreur API /data/station : {payload.get('detail', payload)}")

    return pd.DataFrame(payload["data"])



def post_processed(code_bss: str, end_date: date) -> pd.Timestamp:
    """Request processed. Returns ProcessedResponse."""

    payload = _post("/data/processed", timeout=60,
                     code_bss=code_bss, end_date=end_date.isoformat(),
                     headers=_secret_headers())

    if payload.get("status") != "ok" or "data" not in payload:
        raise RuntimeError(f"Erreur API /data/processed : {payload.get('detail', payload)}")

    return pd.DataFrame(payload["data"])


def post_forecast(code_bss: str, horizon: Literal[14, 30], start_date: date) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Request a forecast. Returns PredictResponse."""
    payload = _post("/data/forecast",timeout=60,
                     code_bss=code_bss, 
                     H=horizon,
                     start_date=start_date.isoformat(),
                     headers=_secret_headers())

    if payload.get("status") != "ok" or "data" not in payload:
        raise RuntimeError(f"Erreur API /data/forecast : {payload.get('detail', payload)}")

    forecast_df = pd.DataFrame(payload["data"])
    forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
    last_train = pd.to_datetime(payload["last_train"])

    return last_train, forecast_df