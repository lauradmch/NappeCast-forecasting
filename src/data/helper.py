#---------------------------------------------------------------------------------
# All useful shared functions
#---------------------------------------------------------------------------------

# Import libraries
from pathlib import Path
from src.config import load_config

import pandas as pd
import logging
import os

CONFIG = load_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    name = Path(local_file).name
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
