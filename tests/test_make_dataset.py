# tests/test_make_dataset.py

import pytest
import pandas as pd
import requests as req_lib
from unittest.mock import patch, MagicMock

from src.data.make_dataset import (
    get_weather,
    get_hubeau,
    merge_data_history,
    merge_data,
    fetch_weather_by_year,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def weather_api_response():
    keys = [
        "weather_code", "temperature_2m_max", "temperature_2m_min",
        "apparent_temperature_max", "apparent_temperature_min",
        "sunrise", "sunset", "daylight_duration", "sunshine_duration",
        "uv_index_max", "uv_index_clear_sky_max", "rain_sum", "showers_sum",
        "snowfall_sum", "precipitation_sum", "precipitation_hours",
        "precipitation_probability_max", "shortwave_radiation_sum",
        "et0_fao_evapotranspiration", "cloud_cover_mean", "dew_point_2m_mean",
        "et0_fao_evapotranspiration_sum", "relative_humidity_2m_mean",
        "snowfall_water_equivalent_sum", "pressure_msl_mean",
        "surface_pressure_mean", "visibility_mean", "wind_speed_10m_mean",
        "soil_moisture_0_to_100cm_mean", "soil_temperature_0_to_100cm_mean",
    ]
    return {"daily": {"time": ["2023-01-01"], **{k: [0.0] for k in keys}}}


@pytest.fixture
def df_hist():
    return pd.DataFrame({
        "code_bss": ["A", "A"],
        "date":     ["2023-01-01", "2023-01-02"],
        "value":    [1.0, 2.0],
    })


# ── get_weather ───────────────────────────────────────────────────────────────

@patch("src.data.make_dataset.requests.get")
def test_get_weather_ok(mock_get, weather_api_response):
    mock_get.return_value = MagicMock(ok=True, json=lambda: weather_api_response)
    df = get_weather("4.8", "43.5", "2023-01-01", "2023-01-01")
    assert isinstance(df, pd.DataFrame) and "rain_sum" in df.columns


@patch("src.data.make_dataset.time.sleep")
@patch("src.data.make_dataset.requests.get")
def test_get_weather_retry_then_success(mock_get, mock_sleep, weather_api_response):
    mock_get.side_effect = [
        req_lib.exceptions.Timeout(),
        MagicMock(ok=True, json=lambda: weather_api_response),
    ]
    df = get_weather("4.8", "43.5", "2023-01-01", "2023-01-01", max_retries=2)
    assert not df.empty


@patch("src.data.make_dataset.time.sleep")
@patch("src.data.make_dataset.requests.get")
def test_get_weather_raises_after_max_retries(mock_get, mock_sleep):
    mock_get.side_effect = req_lib.exceptions.Timeout()
    with pytest.raises(RuntimeError, match="Échec de récupération météo"):
        get_weather("4.8", "43.5", "2023-01-01", "2023-01-01", max_retries=2)


# ── get_hubeau ────────────────────────────────────────────────────────────────

@patch("src.data.make_dataset.time.sleep")
@patch("src.data.make_dataset.requests.get")
def test_get_hubeau_pagination(mock_get, mock_sleep):
    mock_get.side_effect = [
        MagicMock(ok=True, json=lambda: {"data": [{"id": 1}], "next": "http://p2"}),
        MagicMock(ok=True, json=lambda: {"data": [{"id": 2}], "next": None}),
    ]
    df = get_hubeau("http://p1", {})
    assert list(df["id"]) == [1, 2]


@patch("src.data.make_dataset.time.sleep")
@patch("src.data.make_dataset.requests.get")
def test_get_hubeau_raises_after_max_retries(mock_get, mock_sleep):
    mock_get.side_effect = req_lib.exceptions.ConnectionError()
    with pytest.raises(req_lib.exceptions.ConnectionError):
        get_hubeau("http://api", {})


# ── merge_data_history ────────────────────────────────────────────────────────

def test_merge_data_history_dedup_keep_last(df_hist):
    df_new = pd.DataFrame({"code_bss": ["A"], "date": ["2023-01-02"], "value": [99.0]})
    result = merge_data_history(df_hist, df_new, "code_bss", "date")
    
    assert len(result) == 2
    # La ligne du 2023-01-02 doit avoir la valeur de df_new (99.0), pas df_hist (2.0)
    mask = result["date"] == "2023-01-02"
    assert result.loc[mask, "value"].iloc[0] == 99.0