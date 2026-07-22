#---------------------------------------------------------------------------------
# Clean dataset
#---------------------------------------------------------------------------------

# Import libraries
import pandas as pd
import logging

from pathlib import Path
from src.config import load_config
from src.helper import save_interim_data

CONFIG = load_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def piezometer_dataset_cleaning(df: pd.DataFrame,
						      save_csv: bool = True) -> pd.DataFrame:
    """
    Objectives of this function is to clean the piezometer dataset before merging with 
    weather dataset and EDA.
    """
    df = df.copy()
    # Dropping columns
    df["date_mesure"] = pd.to_datetime(df["date_mesure"])
    columns_to_drop = ['code_nature_mesure', 'nom_nature_mesure', 'Unnamed: 0', 'urn_bss', 
                       'timestamp_mesure', 'statut', 'qualification', 'code_continuite', 
                       'nom_continuite', 'code_producteur', 'profondeur_nappe']
    df = df.drop(columns=columns_to_drop)
    
    # Changing the name of the column date (preparation for future merging)
    df = df.rename(columns={'date_mesure': 'date_index'})

    logger.info(f"Cleaning dataset piezometer ended!")

    # Export
    if save_csv :
        save_interim_data(df, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["piezometer"]["interim_filename"])

    return df


def weather_dataset_cleaning(df: pd.DataFrame,
						     save_csv: bool = True) -> pd.DataFrame:
    """
    Objectives of this function is to clean the weather dataset from Open-Meteo before merging with 
    piezometer dataset and EDA.
    """
    df = df.copy()
    # drop columns with too many Nan, index, localization
    df = df.drop(columns=["Unnamed: 0", "precipitation_probability_max", "uv_index_clear_sky_max", 
                          "uv_index_max", "visibility_mean", "showers_sum", "snowfall_sum", 
                          "snowfall_water_equivalent_sum"])
    df = df.rename(columns={"date":"date_index"})
    # drop columns that are too corrolated
    cols_to_drop = [
        'et0_fao_evapotranspiration_sum', 'relative_humidity_2m_mean', 'rain_sum', 'surface_pressure_mean',
        'dew_point_2m_mean', 'precipitation_hours', 'sunshine_duration',
        'weather_code', 'apparent_temperature_min', 'apparent_temperature_max', "temperature_2m_min", "temperature_2m_max"
    ]
    df = df.drop(columns=cols_to_drop, errors='ignore')

    logger.info(f"Cleaning dataset weather ended!")

    # Export
    if save_csv:
        save_interim_data(df, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["weather"]["interim_filename"])

    return df