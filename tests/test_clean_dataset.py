# tests/test_clean_dataset.py

import pytest
import pandas as pd
from unittest.mock import patch

from src.data.clean_dataset import piezometer_dataset_cleaning, weather_dataset_cleaning


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def df_piezo_raw():
    return pd.DataFrame({
        "code_bss":           ["BSS001"],
        "date_mesure":        ["2023-01-01"],
        "niveau_nappe_eau":   [10.5],
        "code_nature_mesure": ["N"], "nom_nature_mesure": ["Nappe"],
        "urn_bss":            ["urn:1"], "timestamp_mesure": [123456],
        "statut":             [1], "qualification":       [1],
        "code_continuite":    ["C"], "nom_continuite":     ["Cont"],
        "code_producteur":    ["P"], "profondeur_nappe":   [5.0],
    })


@pytest.fixture
def df_weather_raw():
    return pd.DataFrame({
        "code_bss": ["BSS001"], "date": ["2023-01-01"],
        "temperature_2m_max": [20.0], "temperature_2m_min": [10.0],
        "apparent_temperature_max": [19.0], "apparent_temperature_min": [9.0],
        "precipitation_sum": [1.0], "precipitation_hours": [2.0],
        "precipitation_probability_max": [50.0],
        "shortwave_radiation_sum": [5.0], "et0_fao_evapotranspiration": [3.0],
        "cloud_cover_mean": [30.0], "pressure_msl_mean": [1013.0],
        "wind_speed_10m_mean": [5.0],
        "soil_moisture_0_to_100cm_mean": [0.3], "soil_temperature_0_to_100cm_mean": [15.0],
        "daylight_duration": [36000.0], "sunshine_duration": [20000.0],
        "sunrise": ["06:00"], "sunset": ["20:00"],
        "weather_code": [1], "uv_index_max": [5.0], "uv_index_clear_sky_max": [6.0],
        "rain_sum": [1.0], "showers_sum": [0.0], "snowfall_sum": [0.0],
        "snowfall_water_equivalent_sum": [0.0], "visibility_mean": [10000.0],
        "dew_point_2m_mean": [8.0], "relative_humidity_2m_mean": [60.0],
        "surface_pressure_mean": [1010.0], "et0_fao_evapotranspiration_sum": [3.0],
        "apparent_temperature_max": [19.0], "apparent_temperature_min": [9.0],
    })


# ── piezometer_dataset_cleaning ───────────────────────────────────────────────

PIEZO_DROPPED = [
    'code_nature_mesure', 'nom_nature_mesure', 'urn_bss', 'timestamp_mesure',
    'statut', 'qualification', 'code_continuite', 'nom_continuite',
    'code_producteur', 'profondeur_nappe', 'date_mesure',
]

@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_piezo_drops_columns(mock_save, df_piezo_raw):
    result = piezometer_dataset_cleaning(df_piezo_raw, save_file=False)
    assert not any(c in result.columns for c in PIEZO_DROPPED)


@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_piezo_creates_date_index(mock_save, df_piezo_raw):
    result = piezometer_dataset_cleaning(df_piezo_raw, save_file=False)
    assert "date_index" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["date_index"])


@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_piezo_does_not_mutate_input(mock_save, df_piezo_raw):
    original_cols = set(df_piezo_raw.columns)
    piezometer_dataset_cleaning(df_piezo_raw, save_file=False)
    assert set(df_piezo_raw.columns) == original_cols


# ── weather_dataset_cleaning ──────────────────────────────────────────────────

WEATHER_DROPPED = [
    "precipitation_probability_max", "uv_index_clear_sky_max", "uv_index_max",
    "visibility_mean", "showers_sum", "snowfall_sum", "date",
    "snowfall_water_equivalent_sum", "et0_fao_evapotranspiration_sum",
    "relative_humidity_2m_mean", "rain_sum", "surface_pressure_mean",
    "dew_point_2m_mean", "precipitation_hours", "sunshine_duration",
    "weather_code", "apparent_temperature_min", "apparent_temperature_max",
    "temperature_2m_min",
]

@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_weather_drops_columns(mock_save, df_weather_raw):
    result = weather_dataset_cleaning(df_weather_raw, save_file=False)
    assert not any(c in result.columns for c in WEATHER_DROPPED)


@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_weather_creates_date_index(mock_save, df_weather_raw):
    result = weather_dataset_cleaning(df_weather_raw, save_file=False)
    assert "date_index" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["date_index"])


@patch("src.data.clean_dataset.save_interim_data_to_s3")
def test_weather_does_not_mutate_input(mock_save, df_weather_raw):
    original_cols = set(df_weather_raw.columns)
    weather_dataset_cleaning(df_weather_raw, save_file=False)
    assert set(df_weather_raw.columns) == original_cols