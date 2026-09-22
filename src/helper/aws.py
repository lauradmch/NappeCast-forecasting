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
from typing import Dict, Optional, Literal
from pathlib import Path
from io import BytesIO
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import date

# ---------------------------- LOGGING --------------------------------
logger = logging.getLogger(__name__)
# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()




# ---------------------------- S3 ---------------------------

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
        logger.warning("Credentials AWS absents — upload S3 de %s ignoré.", Path(local_file).name)
        return

    import boto3

    now = pd.Timestamp.now()
    name = Path(local_file).name
    
    if with_timestamp:
        s3_key = f"{key_prefix}/{now:%Y}/{now:%m}/{name}_{now:%Y%m%d}"      
    else:
        s3_key = f"{key_prefix}/{name}"

    s3 = boto3.client("s3", region_name="eu-west-3")
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
    output_file = output_path / f"{file_name}.csv" 
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


def save_forecast_data_to_s3(df: pd.DataFrame, 
                        output_path: Path, 
                        file_name: str, 
                        with_timestamp: bool=True) -> Path:
    """
    Sauvegarde le forecast au format CSV, puis le persiste sur S3
    (paths.s3)
    """
    output_path.mkdir(parents=True, exist_ok=True)
    output_file =  f"{output_path}/{file_name}.csv" 
    df.to_csv(output_file, index=False)

    s3_cfg = CONFIG.get("s3")
    if s3_cfg:
        upload_file_to_s3(output_file, s3_cfg["bucket"], s3_cfg["prefixes"]["forecast"], with_timestamp)

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

# ---------------------------- RDS ---------------------------

def read_processed_rds(code_bss: str, end_date: date) -> pd.DataFrame:
    """
    Intérroge la base de données RDS
        -> connexion a postgre RDS AWS
        -> passer une date de la forme datetime.strptime(end_date, "%Y-%m-%d").date()
    """
    db_uri = os.environ["NAPPECAST_BACKEND_STORE_URI"]
    engine = create_engine(db_uri)

    query = text("""
        SELECT *
        FROM spli_historic
        WHERE 
            date_index < :end_date
            AND code_bss = :code_bss
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"end_date": end_date, "code_bss": code_bss})

    return df.copy()

def read_forecast_rds(code_bss: str, horizon: Literal[14, 30], start_date: date) -> pd.DataFrame:
    """
    Intérroge la base de données RDS
        -> connexion a postgre RDS AWS
        -> select * from spli_forecast where horizon = horizon and date_train= end_date
        -> passer une date de la forme datetime.strptime(end_date, "%Y-%m-%d").date()
    """
    db_uri = os.environ["NAPPECAST_BACKEND_STORE_URI"]
    engine = create_engine(db_uri)

    query = text("""
        SELECT *
        FROM spli_forecast
        WHERE 
            date_index >= :start_date
            AND code_bss = :code_bss
            horizon = :horizon
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"horizon": horizon, "code_bss": code_bss, "start_date": start_date})

    return df.copy()

def load_csv_to_rds(s3_client, 
                    bucket: str, 
                    filename: str, 
                    sql_create_path: str,
                    unique_index_columns: str,
                    target_table: str) -> dict:
    """
    Télécharge le CSV s3://bucket/key et le charge dans la table cible.
    """
    db_uri = os.environ["NAPPECAST_BACKEND_STORE_URI"]
    engine = create_engine(db_uri)
    
    with engine.begin() as conn:
        conn.execute(text(sql_create_path.read_text(encoding="utf-8")))

    df = read_csv_in_s3(s3_client, bucket, filename)

    if df.empty:
        return {"rows_read": 0, "rows_inserted": 0}

    df = df.where(pd.notnull(df), None)
    records = df.to_dict(orient="records")
 
    # 3. Insérer les lignes par lots, doublons ignorés (ON CONFLICT DO NOTHING)
    metadata = MetaData(schema="public")
    table = Table(target_table, metadata, autoload_with=engine)
 
    inserted_total = 0
    with engine.begin() as conn:
        for start in range(0, len(records), 1000):
            batch = records[start : start + 1000]
            stmt = pg_insert(table).values(batch).on_conflict_do_nothing(
                index_elements=unique_index_columns
            )
            result = conn.execute(stmt)
            if result.rowcount and result.rowcount > 0:
                inserted_total += result.rowcount
 
    return {"rows_read": len(df), "rows_inserted": inserted_total}

def load_forecast_to_rds() -> dict:
    s3 = boto3.client("s3")
    filename = str(Path(CONFIG["paths"]["data"]["forecast"])/f"{CONFIG['paths']['data']['forecast_filename']}.csv")
    sql_path = Path(__file__).parent.parent / "sql" / "create_table_forecast.sql"

    return load_csv_to_rds(s3, 
                           CONFIG["s3"]["bucket"], 
                           filename, 
                           sql_path,
                           ["bss_id","date_index"],
                           "forecast")

def load_processed_to_rds() -> dict:
    s3 = boto3.client("s3")
    filename = str(Path(CONFIG["paths"]["data"]["processed"])/f"{CONFIG['paths']['data']['processed_filename']}.csv")
    sql_path = Path(__file__).parent.parent / "sql" / "create_table_processed.sql"

    return load_csv_to_rds(s3, 
                           CONFIG["s3"]["bucket"], 
                           filename, 
                           sql_path,
                           ["bss_id","date_index"],
                           "processed")



   