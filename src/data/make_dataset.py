"""
Chargement et nettoyage structurel des données.

Transforme les données brutes (data/raw) en données prêtes à l'emploi
pour le feature engineering / l'entraînement (data/processed).

"""
# --------------------------- LIBRARY --------------------------------
import logging
import requests
import os
import numpy as np
import pandas as pd
import time
import argparse

from pathlib import Path
from src.config import load_config
from src.data.clean_dataset import piezometer_dataset_cleaning, weather_dataset_cleaning

from src.helper.aws import load_historical_in_s3,save_raw_data_to_s3, save_interim_data_to_s3
from src.helper.data import get_last_dates, build_start_dates

# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

# ---------------------------- API EXTERNE ---------------------------

def get_weather (lng: str,
                    lat: str,
					start_date: str,
					end_date: str,
					max_retries: int=3) -> pd.DataFrame:

	"""
    Appel de l'hitstorique,  voir apres pour appel du forecast uniquement.
    """

	logger.info(f"Get weather data : {lat}°N {lng}°E - {start_date}->{end_date}")
    
	params = {
		"latitude": lat,
		"longitude": lng,
		"start_date": start_date,
		"end_date": end_date,
		"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_sum", "precipitation_hours", "precipitation_probability_max", "shortwave_radiation_sum", "et0_fao_evapotranspiration", "cloud_cover_mean", "dew_point_2m_mean", "et0_fao_evapotranspiration_sum", "relative_humidity_2m_mean", "snowfall_water_equivalent_sum", "pressure_msl_mean", "surface_pressure_mean", "visibility_mean", "wind_speed_10m_mean", "soil_moisture_0_to_100cm_mean", "soil_temperature_0_to_100cm_mean"],
	}

	attempt = 0
	r = None

	while attempt < max_retries:
		attempt +=1
		try:
			r = requests.get(CONFIG["api"]["weather"]["url_archive"], params=params, timeout=(5, 30))
			r.raise_for_status()
			break

		except requests.exceptions.Timeout:
			logger.warning("Timeout (tentative %s/%s) pour %s;%s",attempt, max_retries, lat, lng)
			time.sleep(10)

	if r is None or not r.ok:
		raise RuntimeError(f"Échec de récupération météo après {attempt} tentatives")
	
	daily = r.json()["daily"]

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


def get_hubeau(first_url: str,
                 params: str) -> pd.DataFrame:
    data_page = []
    next_url = first_url
    headers = {"accept": "application/json"}
 
    while next_url:
        try:
            logger.info(f"Get hubeau data : {next_url}")
            r = requests.get(next_url, params=params, headers=headers, timeout=(5, 30))
            r.raise_for_status()
            
        except requests.exceptions.Timeout:
            print("Timeout, nouvelle tentative...")
            time.sleep(2)
            continue 

        data = r.json()
        data_page.extend(data["data"])
        next_url = data.get("next")
        params = None

        time.sleep(1)

    df = pd.DataFrame(data_page)
    return df


def fetch_weather_by_year(code_bss: str,
                           lng: str,
                           lat: str,
                           end_date: str,
                           failed_calls: list[dict],
						   save_file: bool = True) -> pd.DataFrame:
    
    start   = pd.to_datetime(CONFIG["api"]["weather"]["start_date"])
    end     = pd.to_datetime(end_date)
    frame   = []

    for year in range(start.year, end.year + 1):
        year_start = max(start, pd.Timestamp(year=year, month=1, day=1))
        year_end = min(end, pd.Timestamp(year=year, month=12, day=31))
        current_start = year_start.strftime("%Y-%m-%d")
        current_end = year_end.strftime("%Y-%m-%d")

        try:
            df_year = get_weather(
                lng,
                lat,
                current_start,
                current_end
            )
            df_year["code_bss"] = code_bss

            if save_file == True: 
                df_year.to_csv(Path(CONFIG["paths"]["data"]["external"] / "meteo_{code_bss.replace('/','')}_{pd.to_datetime(year_start).year}.csv"))

            frame.append(df_year)
            time.sleep(5)

        except Exception as e:
            logger.warning(f"Erreur station {code_bss}, année {year}: {e}")

            failed_calls.append({
                "code_bss": code_bss,
                "lng": lng,
                "lat": lat,
                "start_date": current_start,
                "end_date": current_end,
                "error": str(e),
            })

    if not frame:
        return pd.DataFrame()

    return pd.concat(frame, ignore_index=True)


def fetch_station (save_file: bool)-> pd.DataFrame:
    params = {
        "size": 5000, 
        "code_bss" : ",".join(CONFIG["api"]["piezometer"]["code_bss"])
    }
     
    df = get_hubeau(CONFIG["api"]["piezometer"]["url_station"], params)
    df = df.rename(columns={"x": "longitude", "y": "latitude"})

    if save_file:
        save_raw_data_to_s3(df, Path(CONFIG["paths"]["data"]["raw"]), CONFIG["paths"]["station"]["raw_filename"], False)
                
    return df


def fetch_piezometer (df_station: pd.DataFrame,
                      save_file: bool)-> pd.DataFrame:
    frames= []
    for i, (code_bss, lat, lon) in enumerate(zip(df_station["code_bss"], df_station["latitude"], df_station["longitude"])):
        params = {
            "size": 5000, 
            "code_bss" : code_bss
        }
        df_cache = get_hubeau(CONFIG["api"]["piezometer"]["url_piezometre"], params)
        frames.append(df_cache)

    df = pd.concat(frames, ignore_index=True)

    if save_file:
        save_raw_data_to_s3(df, Path(CONFIG["paths"]["data"]["raw"]), CONFIG["paths"]["piezometer"]["raw_filename"], False)
        
    return df


def fetch_weather (df_station: pd.DataFrame,
                   save_file: bool,
                   failed_calls: list[dict])-> pd.DataFrame:
    frames=[]
    failed_calls=[]
    
    for end_date, lat, lng, code_bss in zip(df_station["date_fin_mesure"], 
                                                df_station["latitude"], 
                                                df_station["longitude"], 
                                                df_station["code_bss"]):
        frames.append(fetch_weather_by_year(code_bss,
                                        lng,
                                        lat,
                                        end_date,
                                        failed_calls,
                                        False))

    df = pd.concat(frames, ignore_index=True)
    if save_file:
        save_raw_data_to_s3(df, Path(CONFIG["paths"]["data"]["raw"]), CONFIG["paths"]["weather"]["raw_filename"], False)
      
    return df
  

def merge_data (df_piezometer: pd.DataFrame,
                df_weather: pd.DataFrame,
                save_file: bool) -> pd.DataFrame:
    
    df_piezometer = df_piezometer.copy()
    df_weather = df_weather.copy()

    merged = df_weather.merge(df_piezometer, on=["date_index", "code_bss"], how="left") # left pour toujours avoir une date, ne pas mettre inner
    merged = merged.set_index('date_index', drop=False)
    
    missing = merged["sunrise"].isna().sum()
    if missing > 0:
        mask = merged["sunrise"].isna()
        logger.warning("%d lignes sans correspondance météo", missing)

    logger.info(f"Merging dataset ended!")

    if save_file:
        save_interim_data_to_s3(merged, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["interim_filename"], False)

    return merged

# ----------------------- MODE FORECAST ------------------------

def get_forecast(df_station: pd.DataFrame,
                 path_weather_s3: str, 
                 path_piezometer_s3: str) -> tuple[pd.DataFrame, pd.DataFrame]:
 
    # récupération de l'historique sur S3
    df_weather_hist, df_piezometer_hist = load_historical_in_s3(path_weather_s3, path_piezometer_s3)

    # dernieres dates connues par station
    last_weather_dates      = get_last_dates(df_weather_hist, "code_bss", "date_mesure")
    last_piezometer_dates   = get_last_dates(df_piezometer_hist, "code_bss", "date_mesure")

    # dates de reprise
    start_dates_weather     = build_start_dates(df_station, last_weather_dates, CONFIG["start_date"])
    start_dates_piezometer  = build_start_dates(df_station, last_piezometer_dates, CONFIG["start_date"])

    # fetch uniquement sur la periode recente
    failed_calls: list[dict] = []

    df_weather_new          = fetch_weather_recent(df_station, start_dates_weather, failed_calls)
    df_piezometer_new       = fetch_piezometer_recent(df_station, start_dates_piezometer)
 
    # 5. fusion avec l'historique
    df_weather = merge_with_history(df_weather_hist, df_weather_new, "code_bss", "date_mesure")
    df_piezo = merge_with_history(df_piezo_hist, df_piezo_new, "code_bss", "date_mesure")
 
    return df_weather, df_piezo


# ---------------------------- RUN ---------------------------
def main()-> str: 
    parser = argparse.ArgumentParser(description="Prépare le dataset propre")
    parser.add_argument("--skip-historical",action="store_true",help="Ne pas appeler l'API météo")
    parser.add_argument("--save-csv",action="store_true",help="Persiste les fichiers csv")

    args            = parser.parse_args()
    failed_calls    = []
    df_station      = fetch_station(save_file=args.save_csv)

    if not args.skip_historical:
        logger.info("Mode récupération historique actif")
        df_weather   = fetch_weather(df_station, save_file=args.save_csv, failed_calls=failed_calls)
        df_piezometer= fetch_piezometer(df_station, save_file=args.save_csv)
    else:
        logger.info("Mode récupération forecast actif")
        df_weather      = pd.read_csv(Path(CONFIG["paths"]["data"]["raw"]) / f"{CONFIG['paths']['weather']['raw_filename']}.csv")
        df_piezometer   = pd.read_csv(Path(CONFIG["paths"]["data"]["raw"]) / f"{CONFIG['paths']['piezometer']['raw_filename']}.csv")

    # clean datasets
    df_weather      = weather_dataset_cleaning(df_weather, save_file=args.save_csv)
    df_piezometer   = piezometer_dataset_cleaning(df_piezometer,save_file=args.save_csv)

    # merge datasets
    df_merged       = merge_data(df_piezometer, df_weather, save_file=args.save_csv)

    return df_merged

if __name__ == "__main__":
    main()