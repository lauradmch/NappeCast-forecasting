#---------------------------------------------------------------------------------
# All useful shared functions for aws
#---------------------------------------------------------------------------------

# ---------------------------- LIBRARY ---------------------------
import pandas as pd
import logging
import os
import boto3
import io

from pathlib import Path
from src.config import load_config
from botocore.exceptions import ClientError

# ---------------------------- LOGGING --------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

# ---------------------------- AWS ---------------------------

def upload_file_to_s3(local_file: Path, 
                      bucket: str, 
                      key_prefix: str, 
                      with_timestamp: bool=True) -> None:
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
    
    if with_timestamp:
        s3_key = f"{key_prefix}/{now:%Y}/{now:%m}/{name}_{now:%Y%m%d}"      
    else:
        s3_key = f"{key_prefix}/{name}"

    s3 = boto3.client("s3")
    s3.upload_file(str(local_file), bucket, s3_key)
    logger.info("Fichier persisté sur s3://%s/%s", bucket, s3_key)


def save_raw_data_to_s3(df: pd.DataFrame, 
                  output_path: Path, 
                  file_name: str, 
                  with_timestamp: bool=True) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file =  f"{output_path}/{file_name}.csv" 
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["raw"], with_timestamp)

    return output_file


def save_interim_data_to_s3(df: pd.DataFrame, 
                      output_path: Path, 
                      file_name: str, 
                      with_timestamp: bool=True) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file =  f"{output_path}/{file_name}.csv" 
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["interim"], with_timestamp)

    return output_file


def save_processed_data_to_s3(df: pd.DataFrame, 
                        output_path: Path, 
                        file_name: str, 
                        with_timestamp: bool=True) -> Path:
    """
    Sauvegarde le dataset nettoyé au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file =  f"{output_path}/{file_name}.csv" 
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["processed"], with_timestamp)

    return output_file


def file_exists_in_s3(s3_client, 
                   bucket: str, 
                   filename: str) -> bool:
    try:
        s3_client.head_object(Bucket=bucket, Key=filename)
        return True
    
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise

 
def read_csv_in_s3(s3_client, 
                     bucket: str, 
                     filename: str) -> pd.DataFrame:
    """
    Lit un fichier sur le bucket s3
    """
    logger.info(f"Lecture du fichier S3 {filename} dans le bucket {bucket}")
    obj = s3_client.get_object(Bucket=bucket, Key=str(filename))
    return pd.read_csv(io.BytesIO(obj["Body"].read()))

 
def load_historical_in_s3(weather_raw_filename: str, 
                          piezometer_raw_filename: str) -> tuple[pd.DataFrame, pd.DataFrame]:

    """
    Charge les historiques weather et piezometre depuis S3.
    """
    s3 = boto3.client("s3")
   
    if not file_exists_in_s3(s3, CONFIG["s3"]["bucket"], weather_raw_filename):
        raise FileNotFoundError(f"Historique weather introuvable sur S3 : s3://{CONFIG['s3']['bucket']}/{weather_raw_filename}")
    
    if not file_exists_in_s3(s3, CONFIG["s3"]["bucket"], piezometer_raw_filename):
        raise FileNotFoundError(f"Historique piezometre introuvable sur S3 : s3://{CONFIG['s3']['bucket']}/{piezometer_raw_filename}")
 
    df_weather_hist = read_csv_in_s3(s3, CONFIG["s3"]["bucket"], weather_raw_filename)
    df_piezo_hist = read_csv_in_s3(s3, CONFIG["s3"]["bucket"], piezometer_raw_filename)
 
    return df_weather_hist, df_piezo_hist
