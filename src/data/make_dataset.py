"""
Chargement et nettoyage structurel des données.

Transforme les données brutes (data/raw) en données prêtes à l'emploi
pour le feature engineering / l'entraînement (data/processed).

"""
# --------------------------- XXXXXXX --------------------------------

# --------------------------- LIBRARY --------------------------------
import logging
import requests
import os
import numpy as np
import pandas as pd

from pathlib import Path
from src.config import load_config

# --------------------------- LOGGING --------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
CONFIG = load_config()


# ---------------------------- API EXTERNE ---------------------------

def get_meteo (lng: str,
                    lat: str,
					start_date: str,
					end_date: str) -> pd.DataFrame :
    
    weather_cfg = CONFIG["api"]["weather"]

    url = weather_cfg["url_archive"]
	
    params = {
		"latitude": lat,
		"longitude": lng,
		"start_date": start_date,
		"end_date": end_date,
		"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_sum", "precipitation_hours", "precipitation_probability_max", "shortwave_radiation_sum", "et0_fao_evapotranspiration", "cloud_cover_mean", "dew_point_2m_mean", "et0_fao_evapotranspiration_sum", "relative_humidity_2m_mean", "snowfall_water_equivalent_sum", "pressure_msl_mean", "surface_pressure_mean", "visibility_mean", "wind_speed_10m_mean", "soil_moisture_0_to_100cm_mean", "soil_temperature_0_to_100cm_mean"],
	}

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    daily = response.json()["daily"]

    return pd.DataFrame({
		"date": pd.to_datetime(daily["time"]),
		"latitude": lat,
		"longitude": lng,
		"weather_code": daily["weather_code"],
		"temperature_2m_max": daily["temperature_2m_max"],
		"temperature_2m_min": daily["temperature_2m_min"],
		"apparent_temperature_max": daily["apparent_temperature_max"],
		"apparent_temperature_min": daily["apparent_temperature_min"],
		"sunrise": daily["sunrise"],
		"sunset": daily["sunset"],
		"daylight_duration": daily["daylight_duration"],
		"sunshine_duration": daily["sunshine_duration"],
		"uv_index_max": daily["uv_index_max"],
		"uv_index_clear_sky_max": daily["uv_index_clear_sky_max"],
		"rain_sum": daily["rain_sum"],
		"showers_sum": daily["showers_sum"],
		"snowfall_sum": daily["snowfall_sum"],
		"precipitation_sum": daily["precipitation_sum"],
		"precipitation_hours": daily["precipitation_hours"],
		"precipitation_probability_max": daily["precipitation_probability_max"],
		"shortwave_radiation_sum": daily["shortwave_radiation_sum"],
		"et0_fao_evapotranspiration": daily["et0_fao_evapotranspiration"],
		"cloud_cover_mean": daily["cloud_cover_mean"],
		"dew_point_2m_mean": daily["dew_point_2m_mean"],
		"et0_fao_evapotranspiration_sum": daily["et0_fao_evapotranspiration_sum"],
		"relative_humidity_2m_mean": daily["relative_humidity_2m_mean"],
		"snowfall_water_equivalent_sum": daily["snowfall_water_equivalent_sum"],
		"pressure_msl_mean": daily["pressure_msl_mean"],
		"surface_pressure_mean": daily["surface_pressure_mean"],
		"visibility_mean": daily["visibility_mean"],
		"wind_speed_10m_mean": daily["wind_speed_10m_mean"],
		"soil_moisture_0_to_100cm_mean": daily["soil_moisture_0_to_100cm_mean"],
		"soil_temperature_0_to_100cm_mean": daily["soil_temperature_0_to_100cm_mean"],
	})