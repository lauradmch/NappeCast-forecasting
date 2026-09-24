"""
API de test (acces databse, acces inférence ...)
"""

import threading
import pandas as pd 
import boto3
import logging
import os

from fastapi import FastAPI, Depends, Header, HTTPException
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Optional, Literal
from pathlib import Path
from src.config import load_config

from src.data.make_dataset import build_dataset
from src.data.feat_dataset import feat_dataset
from src.helper.aws import (
    load_processed_to_rds, 
    load_station_to_rds, 
    load_forecast_to_rds,
    read_processed_rds,
    read_forecast_rds,
    read_station_rds,
    upload_file_to_s3
)

from src.api.model_loader import get_model_info, load_model
from src.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    StationResponse,
    StationRecord,
    InterimResponse,
    InterimRecord,
    ProcessedResponse, 
    ProcessedRecord,
    ForecastResponse,
    ForecastRecord,
    TuningResponse,
    LoadResponse,
    TransfertLogResponse
)

from src.models.prophet_predict import predict
from src.models.prophet_tune import run_tuning

#--------------------- VARIABLES ---------------------
CONFIG = load_config()
PIPELINE_SECRET = os.environ["PIPELINE_SECRET"]

_tuning_lock = threading.Lock()  # pour éviter que deux tuning se chevauchent (et écrasent le CSV)

# ---------------------------- LOGGING --------------------------------
LOG_DIR         = CONFIG["api"]["logs"]["path"]
LOG_NAME        = CONFIG["api"]["logs"]["filename"]

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, 
                    format=CONFIG["system"]["logging_format"],
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler(os.path.join(LOG_DIR, LOG_NAME), mode="a")
                    ])
logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
logger = logging.getLogger(__name__)
logger.info("Logger initialisé OK")
#--------------------- ENDPOINTS & HELPERS ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    for H in (14, 30):
        try:
            load_model(model="Prophet", horizon=H)
        except Exception as e:
            logger.warning("Model pre-loading H=%d failed : %s", H, e)

    yield  # l'API tourne ici -- rien à faire à l'arrêt pour ce projet

app = FastAPI(
    title="NappCast",
    description="Sert les prédictions du modèle entraîné (source configurable : local, S3, MLflow).",
    version="1.0.0",
    lifespan=lifespan
)

def verify_secret(x_pipeline_secret: str = Header(...)):
    if x_pipeline_secret != PIPELINE_SECRET:
        raise HTTPException(status_code=403, detail="Secret invalide")


@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
def health():
    """
    Vérifie que l'API répond — ne garantit pas que le modèle est chargé (voir /model/info).
    """
    return {"status": "ok"}

# -------------------------------------------------
# models
# -------------------------------------------------
@app.get("/model/info", response_model=ModelInfoResponse, tags=["monitoring"])
def model_info(model: Optional[str] = None, source: Optional[str] = None, horizon: Optional[int] = None):
    """État du modèle en cache pour le type/source donnés (ou le modèle actif par défaut si omis)."""
    return get_model_info(model=model, source=source, horizon=horizon)


@app.post("/model/reload", response_model=ModelInfoResponse, tags=["monitoring"])
def model_reload(model: Optional[str] = None, source: Optional[str] = None, horizon: Optional[int] = None, _: None = Depends(verify_secret)):
    """Force un rechargement du modèle (type/source donnés, ou modèle actif par défaut) — utile après un nouvel entraînement."""
    try:
        load_model(model=model, source=source, horizon=horizon, force_reload=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec du rechargement du modèle : {e}")
    return get_model_info(model=model, source=source, horizon=horizon)

# -------------------------------------------------
# Pipeline
# -------------------------------------------------
@app.post("/pipeline/collect", response_model=InterimResponse, tags=["pipeline"])
def collect(_: None = Depends(verify_secret)):
    """lance la collect et le nettoyage"""
    try:
        _, df_interim = build_dataset(skip_historical=True, save_csv=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la collecte des données : {e}")

    df_interim = df_interim.astype(object).where(pd.notna(df_interim), None)

    try:
        records = [InterimRecord(**row) for row in df_interim.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return InterimResponse(status="ok", n_rows=len(records), data=records)
    
@app.post("/pipeline/transform", response_model=ProcessedResponse, tags=["pipeline"])
def transform(_: None = Depends(verify_secret)):
    """lance le feature engineering sur les données interim"""
    try:
        df_processed = feat_dataset(save_csv=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du feature engineering : {e}")

    df_processed = df_processed.where(pd.notnull(df_processed), None)

    try:
        records = [ProcessedRecord(**row) for row in df_processed.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return ProcessedResponse(status="ok", n_rows=len(records), data=records)


@app.post("/pipeline/forecast", response_model=ForecastResponse, tags=["pipeline"])
def forecast(H: Literal[14, 30], _: None = Depends(verify_secret)):
    """Effectue le predict avec les dernières données processed"""
    try:
        last_train, df_forecast = predict(H, save_csv=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul de la prévision : {e}")

    df_forecast = df_forecast.where(pd.notnull(df_forecast), None)

    try:
        records = [ForecastRecord(**row) for row in df_forecast.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return ForecastResponse(status="ok", horizon=H, last_train=last_train,
                             n_rows=len(records), data=records)


@app.post("/pipeline/tuning", response_model=TuningResponse, tags=["training"])
def run_model_tuning(H: Literal[14, 30], source: Literal["s3", "local"] = "s3", _: None = Depends(verify_secret)):
    """Exécute le tuning du modèle pour un horizon donné"""
    if not _tuning_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Tuning déjà en cours")
    try:
        run_tuning(H, source)
        return TuningResponse(status="ok", horizon=H)
    except Exception as e:
        logger.exception("Tuning failed for H=%d: %s", H, e)
        raise HTTPException(status_code=500, detail=f"Tuning failed for H={H}:{e}")
    finally:
        _tuning_lock.release()


@app.post("/pipeline/load", response_model=LoadResponse, tags=["pipeline"])
def load(_: None = Depends(verify_secret)):
    """Historise dans RDS les données"""
    try:
        insert_station   = load_station_to_rds()["rows_inserted"]
        insert_processed = load_processed_to_rds()["rows_inserted"]
        insert_forecast  = sum(load_forecast_to_rds(H)["rows_inserted"] for H in (14, 30))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des données dans RDS : {e}")

    return LoadResponse(status="ok", nb_station=insert_station, nb_processed=insert_processed, nb_forecast=insert_forecast)


@app.post("/data/transfert_log", response_model=TransfertLogResponse, tags=["pipeline"])
def transfert_log(_: None = Depends(verify_secret)):
    """Historise dans S3 le fichier de log"""
    try:
        upload_file_to_s3(
            local_file=Path("logs/nappecast.log"),
            bucket=CONFIG["s3"]["bucket"],
            key_prefix=CONFIG["s3"]["prefixes"]["logs"],
            with_timestamp=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi du log vers S3 : {e}")

    return TransfertLogResponse(status="ok", file="logs/nappecast.log")


# -------------------------------------------------
# Get data from AWS RDS
# -------------------------------------------------     
@app.post("/data/station", response_model=StationResponse, tags=["data"])
def get_station(code_bss: str):
    """Récupère les datas de la table station depuis le serveur de base de données AWS RDS"""
    try:
        df_station = read_station_rds(code_bss)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données station : {e}")

    if df_station is None or df_station.empty:
        raise HTTPException(status_code=404, detail=f"Aucune station trouvée pour code_bss={code_bss}")

    try:
        records = [StationRecord(**row) for row in df_station.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return StationResponse(status="ok", n_rows=len(records), data=records)


@app.post("/data/processed", response_model=ProcessedResponse, tags=["data"])
def get_processed(code_bss: str, end_date: date):
    """Récupère les datas de la table processed depuis le serveur de base de données AWS RDS"""
    try:
        df_processed = read_processed_rds(code_bss, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données processed : {e}")

    if df_processed is None or df_processed.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée processed trouvée pour code_bss={code_bss}")

    try:
        records = [ProcessedRecord(**row) for row in df_processed.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return ProcessedResponse(status="ok", n_rows=len(records), last_train=end_date, data=records)


@app.post("/data/forecast", response_model=ForecastResponse, tags=["data"])
def get_forecast(code_bss: str, horizon: Literal[14, 30], start_date: date):
    """Récupère les datas de la table forecast depuis le serveur de base de données AWS RDS"""
    try:
        df_forecast = read_forecast_rds(code_bss, horizon, start_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des prévisions : {e}")

    if df_forecast is None or df_forecast.empty:
        raise HTTPException(status_code=404, detail=f"Aucune prévision trouvée pour code_bss={code_bss}")

    try:
        records = [ForecastRecord(**row) for row in df_forecast.to_dict(orient="records")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de formatage des données : {e}")

    return ForecastResponse(status="ok", n_rows=len(records), horizon=horizon, last_train=start_date, data=records)