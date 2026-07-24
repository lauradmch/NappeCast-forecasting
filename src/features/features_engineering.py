#---------------------------------------------------------------------------------
# Features engineering
#---------------------------------------------------------------------------------

# Import libraries
from pathlib import Path
import pandas as pd
import numpy as np

from pathlib import Path
import logging
from src.config import load_config
from src.helper import save_interim_data

CONFIG = load_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def featuring_dataset(df: pd.DataFrame, 
                      save_file: bool = True) -> pd.DataFrame:
    """
    xxx
    """
    df = df.copy()
    
    # Setting 'date_index' as index of the dataframe
    df["date_index"] = pd.to_datetime(df["date_index"])
    df = df.set_index("date_index")
    
    # Treatment of duplicated rows (kept only one reading per day)
    df = df[~df.index.duplicated(keep="first")]
    
    # PART FOR GAPS !!!!!!####################
    # PART FOR GAPS !!!!!!####################
    # PART FOR GAPS !!!!!!####################
    
    # Computation of cumulative precipitation (during the last 7-30-90 days)
    df['P_cum_7d'] = df['precipitation_sum'].rolling(window=7).sum()
    df['P_cum_30d'] = df['precipitation_sum'].rolling(window=30).sum()
    df['P_cum_90d'] = df['precipitation_sum'].rolling(window=90).sum()
    
    # Computation of cumulative effective precipitation (during the last 30 & 90 days)
    df['Peff_cum_30d'] = (df['precipitation_sum'] - df['et0_fao_evapotranspiration']).rolling(window=30).sum()
    df['Peff_cum_90d'] = (df['precipitation_sum'] - df['et0_fao_evapotranspiration']).rolling(window=90).sum()
    
    # Computation of the mean temperature (during the last 7 and 30 days)
    df['Temperature_mean_7d'] = round(df['soil_temperature_0_to_100cm_mean'].rolling(window=7).mean(), 2)
    df['Temperature_mean_30d'] = round(df['soil_temperature_0_to_100cm_mean'].rolling(window=7).mean(), 2)

    # Filling the NaN generated during the earliest period of the dataframe (no computation of the cumulative data)
    df['P_cum_7d']              = df['P_cum_7d'].fillna(df['P_cum_7d'].dropna().iloc[0])
    df['P_cum_30d']             = df['P_cum_30d'].fillna(df['P_cum_30d'].dropna().iloc[0])
    df['P_cum_90d']             = df['P_cum_90d'].fillna(df['P_cum_90d'].dropna().iloc[0])
    df['Peff_cum_30d']           = df['Peff_cum_30d'].fillna(df['Peff_cum_30d'].dropna().iloc[0])
    df['Peff_cum_90d']          = df['Peff_cum_90d'].fillna(df['Peff_cum_90d'].dropna().iloc[0])
    df['Temperature_mean_7d']  = df['Temperature_mean_7d'].fillna(df['Temperature_mean_7d'].dropna().iloc[0])
    df['Temperature_mean_30d']  = df['Temperature_mean_30d'].fillna(df['Temperature_mean_30d'].dropna().iloc[0])




####### check for the file name and folder destination ###################
    # Export
    if save_file:
        save_interim_data(df, Path(CONFIG["paths"]["data"]["interim"]), CONFIG["paths"]["weather"]["interim_filename"], False)

    return df