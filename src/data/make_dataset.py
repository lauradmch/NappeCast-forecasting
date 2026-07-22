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
import time
import argparse

from pathlib import Path
from src.config import load_config
from src.data.clean_dataset import piezometer_dataset_cleaning, weather_dataset_cleaning

# --------------------------- LOGGING --------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
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
						   export_csv: bool = True) -> pd.DataFrame:
    
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

            if export_csv == True: 
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


def fetch_station (save_csv: bool)-> pd.DataFrame:
    params = {
        "size": 5000, 
        "code_bss" : ",".join(CONFIG["api"]["piezometer"]["code_bss"])
    }
     
    df = get_hubeau(CONFIG["api"]["piezometer"]["url_station"], params)
    df = df.rename(columns={"y": "longitude", "x": "latitude"})
    if save_csv:
        file = Path(CONFIG["paths"]["data"]["external"] / CONFIG["paths"]["station"]["external_filename"])
        df.to_csv(file)
    return df


def fetch_piezometer (df_station: pd.DataFrame,
                      save_csv: bool)-> pd.DataFrame:
    frames= []
    for i, (code_bss, lat, lon) in enumerate(zip(df_station["code_bss"], df_station["latitude"], df_station["longitude"])):
        params = {
            "size": 5000, 
            "code_bss" : code_bss
        }
        df_cache = get_hubeau(CONFIG["api"]["piezometer"]["url_piezometre"], params)
        frames.append(df_cache)

    df = pd.concat(frames, ignore_index=True)

    if save_csv:
        file = Path(CONFIG["paths"]["data"]["external"] / CONFIG["paths"]["piezometer"]["external_filename"])
        df.to_csv(file)
    return df


def fetch_weather (df_station: pd.DataFrame,
                   save_csv: bool,
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
    if save_csv:
        file = Path(CONFIG["paths"]["data"]["external"] / CONFIG["paths"]["weather"]["external_filename"])
        df.to_csv(file)
  

def merge_data (df_piezometer: pd.DataFrame,
                df_weather: pd.DataFrame) -> pd.DataFrame:

    df_piezometer = df_piezometer.copy()
    df_piezometer["date_index"] = pd.to_datetime(df_piezometer["date_index"])

    df_weather = df_weather.copy()
    df_weather["date_index"] = pd.to_datetime(df_weather["date_index"])

    merged = df_piezometer.merge(df_weather, on=["date_index", "code_bss"], how="inner")

    missing = merged["sunrise"].isna().sum()
    if missing > 0:
        mask = merged["sunrise"].isna()
        print(merged[mask][["date_index","code_bss"]])

        logger.warning("%d lignes sans correspondance météo", missing)

    logger.info(f"Merging dataset ended!")

    return merged


# ---------------------------- AWS ---------------------------
def upload_file_to_s3(local_file: Path, bucket: str, key_prefix: str) -> None:
    """
    Persiste un fichier local dans le bucket S3 configuré, sous la clé :
        {key_prefix}/{année}/{mois}/{nom}_{AAAAMMJJ}.csv
    où {nom} est déduit du dernier segment de key_prefix (ex: "meteo" pour
    key_prefix="external/meteo").
    """
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        logger.warning("Credentials AWS absents — upload S3 de %s ignoré.", local_file.name)
        return

    import boto3

    now = pd.Timestamp.now()
    name = Path(key_prefix).name
    s3_key = f"{key_prefix}/{now:%Y}/{now:%m}/{name}_{now:%Y%m%d}.csv"

    s3 = boto3.client("s3")
    s3.upload_file(str(local_file), bucket, s3_key)
    logger.info("Fichier persisté sur s3://%s/%s", bucket, s3_key)


def save_raw_data(df: pd.DataFrame, output_path: Path, file_name: str) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / file_name
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["raw"])

    return output_file


def save_processed_data(df: pd.DataFrame, output_path: Path, file_name: str) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / file_name
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["processed"])

    return output_file


def save_interim_data(df: pd.DataFrame, output_path: Path, file_name: str) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / file_name
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["interim"])

    return output_file

# ---------------------------- RUN ---------------------------
def main(): 
    parser = argparse.ArgumentParser(description="Prépare le dataset propre")
    parser.add_argument("--skip-historical",action="store_false",help="Ne pas appeler l'API météo")
    parser.add_argument("--save-csv",action="store_true",help="Persiste les fichiers csv")

    args            = parser.parse_args()
    failed_calls    = []
    df_station      = fetch_station(save_csv=args.save_csv)
    
    if not args.skip_historical:
        logger.info("Récupération historique météo/piezo")
        df_weather = fetch_weather(df_station, save_csv=args.save_csv, failed_calls=failed_calls)
        df_piezometer = fetch_piezometer(df_station, save_csv=args.save_csv)
    else:
        logger.info("Récupération forecast météo/piezo")
        # chargement des données historisés / voir persistance sur S3 (pas en local)
        df_weather      = pd.read_csv(Path(CONFIG["paths"]["data"]["external"])/CONFIG["paths"]["weather"]["external_filename"])
        df_piezometer   = pd.read_csv(Path(CONFIG["paths"]["data"]["external"])/CONFIG["paths"]["piezometer"]["external_filename"])
        # TODO: prévoir d'interroger uniquement l'API de forecast sur les données manquantes

    # clean datasets
    df_weather      = weather_dataset_cleaning(df_weather)
    df_piezometer   = piezometer_dataset_cleaning(df_piezometer)

    # merge dataset
    df_merged       = merge_data(df_piezometer, df_weather)

    # df_merged.to_csv(Path(CONFIG["paths"]["data"]["raw"]) / CONFIG["paths"]["raw_filename"])
    

    output_file = save_raw_data(df_merged, CONFIG["paths"]["data"]["raw"], CONFIG["paths"]["raw_filename"])

if __name__ == "__main__":
    main()