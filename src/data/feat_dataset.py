"""
Features ingineering

"""
# --------------------------- LIBRARY --------------------------------
import logging
import requests
import os
import numpy as np
import pandas as pd
import time
import argparse
import boto3

from pathlib import Path
from src.config import load_config
from src.data.clean_dataset import piezometer_dataset_cleaning, weather_dataset_cleaning
from src.features.features_engineering import featuring_dataset


from src.helper.aws import read_csv_in_s3
from src.helper.data import get_last_dates, build_start_dates



# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()
INTERIM_FILENAME = Path(CONFIG["paths"]["data"]["interim"]) / f"{CONFIG['paths']['interim_filename']}.csv"

# ---------------------------- RUN ---------------------------
def main()-> str: 
    parser = argparse.ArgumentParser(description="Ajoute le feature engineering")
    parser.add_argument("--save-csv",action="store_true",help="Persiste les fichiers csv")

    args            = parser.parse_args()
    s3              = boto3.client("s3")
    s3_cfg = CONFIG.get("s3")
     
    df_interim      = read_csv_in_s3(s3, s3_cfg["bucket"], INTERIM_FILENAME)
    df_processed    = featuring_dataset(df_interim, save_file=args.save_csv)

    return df_processed

if __name__ == "__main__":
    main()