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
from src.features.features_engineering import feature_engineering
from src.helper.aws import read_csv_in_s3

# ---------------------------- LOGGING --------------------------------
logger = logging.getLogger(__name__)
# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()
INTERIM_FILENAME = Path(CONFIG["paths"]["data"]["interim"]) / f"{CONFIG['paths']['interim_filename']}.csv"

# ---------------------------- RUN ---------------------------

def feat_dataset(save_csv: bool = False) -> pd.DataFrame:
    s3              = boto3.client("s3")
    df_interim      = read_csv_in_s3(s3, CONFIG["s3"]["bucket"], INTERIM_FILENAME)
    df_processed    = feature_engineering(df_interim, save_file=save_csv)
    return df_processed

def main()-> str: 
    parser = argparse.ArgumentParser(description="Ajoute le feature engineering")
    parser.add_argument("--save-csv",action="store_true",help="Persiste les fichiers csv")
    args = parser.parse_args()
    return feat_dataset(save_csv=args.save_csv)

if __name__ == "__main__":
    main()