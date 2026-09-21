#---------------------------------------------------------------------------------
# All useful shared functions for data
#---------------------------------------------------------------------------------


# ---------------------------- LIBRARY ---------------------------
import pandas as pd
import logging
import os
import boto3
import io

from typing import Dict, Optional, Literal
from pathlib import Path
from src.config import load_config
from botocore.exceptions import ClientError

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

def get_historic_rds(horizon: Literal[14, 30], end_date: str) -> pd.DataFrame:
    """
    Intérroge la base de données RDS
        -> connexion a postgre RDS AWS
        -> select * from spli_historic where horizon = horizon and date_train= end_date
    """



    df_return = df_historic.copy()
    return df_return


def get_forecast_rds(horizon: Literal[14, 30], end_date: str) -> pd.DataFrame:
    """
    Intérroge la base de données RDS
        -> connexion a postgre RDS AWS
        -> select * from spli_forecast where horizon = horizon and date_train= end_date
    """

    df_return = df_forecast.copy()

    return df_forecast
 

 
