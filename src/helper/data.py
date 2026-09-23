#---------------------------------------------------------------------------------
# All useful shared functions for data
#---------------------------------------------------------------------------------


# ---------------------------- LIBRARY ---------------------------
import pandas as pd
import logging
import os
import boto3
import io


from src.config import load_config

# ---------------------------- LOGGING --------------------------------
logger = logging.getLogger(__name__)
# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

# ---------------------------- AWS ---------------------------


def get_last_dates(df: pd.DataFrame, code_col: str, date_col: str) -> dict:
    """
    Derniere date connue par station
    """
    dates = pd.to_datetime(df[date_col])
    return dates.groupby(df[code_col]).max().to_dict()


def build_start_dates(df_station: pd.DataFrame, last_dates: dict, default_start: str) -> pd.Series:
    """
    Date de reprise par station
        -> derniere date historique + 1 jour
        -> si station absente de l'historique : start_date du config
    """
    default = pd.to_datetime(default_start)
 
    def start_for(code_bss):
        last = last_dates.get(code_bss)
        return last + pd.Timedelta(days=1) if last is not None else default
 
    return df_station["code_bss"].map(start_for)

def station_identity(df: pd.DataFrame) -> tuple[str, str]:
    """(code_bss, bss_id) — raises if the dataset holds more than one station."""
    codes = df["code_bss"].dropna().unique()
    if len(codes) != 1:
        raise ValueError(f"Expected exactly one code_bss, got {list(codes)}")
    bss_id = df.loc[df["code_bss"] == codes[0], "bss_id"].dropna().iloc[0]
    return str(codes[0]), str(bss_id)