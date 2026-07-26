#---------------------------------------------------------------------------------
# Clean dataset
#---------------------------------------------------------------------------------

# Import libraries
import pandas as pd
import logging

from pathlib import Path
from src.config import load_config
from src.helper.aws import save_interim_data_to_s3

# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

# ---------------------------- GET DATA ---------------------------

def piezometer_dataset_cleaning(df: pd.DataFrame,
						      save_file: bool = True) -> pd.DataFrame:
    """
    Objectives of this function is to clean the piezometer dataset before merging with 
    weather dataset and EDA.
    """

    df = df.copy()
    df["date_index"] = pd.to_datetime(df["date_mesure"])  

    # Dropping columns
    columns_to_drop = ['code_nature_mesure', 'nom_nature_mesure',  'urn_bss', 
                       'timestamp_mesure', 'statut', 'qualification', 'code_continuite', 
                       'nom_continuite', 'code_producteur', 'profondeur_nappe', 'date_mesure']
    df = df.drop(columns=columns_to_drop)

    # Export
    if save_file :
        save_interim_data_to_s3(df, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["piezometer"]["interim_filename"], False)

    logger.info(f"Cleaning dataset piezometer ended!")
    return df


def weather_dataset_cleaning(df: pd.DataFrame,
						     save_file: bool = True) -> pd.DataFrame:
    """
    Objectives of this function is to clean the weather dataset from Open-Meteo before merging with 
    piezometer dataset and EDA.
    """
    df = df.copy() 
    df["date_index"] = pd.to_datetime(df["date"])  
    
    # drop columns with too many Nan, index, localization
    df = df.drop(columns=["precipitation_probability_max", "uv_index_clear_sky_max", 
                          "uv_index_max", "visibility_mean", "showers_sum", "snowfall_sum", "date",
                          "snowfall_water_equivalent_sum"])

    # drop columns that are too corrolated
    cols_to_drop = [
        'et0_fao_evapotranspiration_sum', 'relative_humidity_2m_mean', 'rain_sum', 'surface_pressure_mean',
        'dew_point_2m_mean', 'precipitation_hours', 'sunshine_duration',
        'weather_code', 'apparent_temperature_min', 'apparent_temperature_max', "temperature_2m_min"
    ]
    df = df.drop(columns=cols_to_drop)

    # Export
    if save_file:
        save_interim_data_to_s3(df, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["weather"]["interim_filename"], False)

    logger.info(f"Cleaning dataset weather ended!")
    return df