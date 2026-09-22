"""
API de test (acces databse, acces inférence ...)
"""

import uvicorn
import pandas as pd 
import boto3
import urllib 
import logging
import os
import mlflow
import numpy as np

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from prophet import Prophet
from mlflow.exceptions import RestException
from mlflow import MlflowClient


from typing import Dict, Optional, Literal
from pathlib import Path
from src.config import load_config, mlflow_tracking_uri

from src.data.make_dataset import build_dataset
from src.data.feat_dataset import feat_dataset
from src.helper.aws import read_csv_in_s3
from src.helper.data import get_historic_rds, get_forecast_rds

from src.api.model_loader import get_model_info, load_model
from src.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictResponse,
    PredictRecord,
    TrainingResponse,
    InterimRecord, 
    InterimResponse,
    ProcessedResponse, 
    ProcessedRecord,
    HistoricResponse,
    ForecastResponse,
    LoadResponse
)
from src.models.production import promote
from src.models.prophet_predict import predict
from src.models.prophet import (build_train_frame,
                                build_daily,
                                TARGET,
)

#--------------------- VARIABLES ---------------------
CONFIG = load_config()
S3_SESSION              = boto3.client("s3") 
BUCKET_NAME             = CONFIG["s3"]["bucket"]
PROCESSED_FILENAME      = Path(CONFIG["paths"]["data"]["processed"]) / f"{CONFIG['paths']['processed_filename']}.csv"
# TODO: commit tuning_results files and add path in config
TUNING_CSV_PATH         = Path(__file__).resolve().parents[2] / "src" / "models"

EXPERIMENT_NAME = CONFIG["mlflow"]["experiment_name"]
PIPELINE_SECRET = os.environ["PIPELINE_SECRET"]

_cache: dict = {}  # {"etag": str, "df": pd.DataFrame}

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

def load_cached_dataset() -> pd.DataFrame:
    head = S3_SESSION.head_object(Bucket=BUCKET_NAME, Key=PROCESSED_FILENAME)
    etag = head["ETag"]
    if _cache.get("etag") != etag:
        logger.info("Dataset cache miss (etag=%s) — reloading from S3", etag)
        _cache["df"]   = read_csv_in_s3(S3_SESSION, BUCKET_NAME, PROCESSED_FILENAME)
        _cache["etag"] = etag
    return _cache["df"]

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
async def collect(_: None = Depends(verify_secret)):
    """lance la collect et le nettoyage""" 
    _, df_interim = build_dataset(skip_historical=True, save_csv=True)
    df_interim = df_interim.where(pd.notnull(df_interim), None)
    records = [InterimRecord(**row) for row in df_interim.to_dict(orient="records")]
    return InterimResponse(status="ok", n_rows=len(records), data=records)
    
@app.post("/pipeline/transform", response_model=ProcessedResponse, tags=["pipeline"])
async def transform(_: None = Depends(verify_secret)):
    """lance le feature engineering sur les données interim"""
    df_processed = feat_dataset(save_csv=True)
    df_processed = df_processed.where(pd.notnull(df_processed), None)
    records = [ProcessedRecord(**row) for row in df_processed.to_dict(orient="records")]
    return ProcessedResponse(status="ok", n_rows=len(records), data=records)

@app.post("/pipeline/forecast", response_model=PredictResponse, tags=["pipeline"])
async def forecast(H: Literal[14, 30], _: None = Depends(verify_secret)):
    """Effectue le predict avec les dernières données processed"""
    last_train, forecast = predict(H, save_csv=True)
    records = [PredictRecord(**row) for row in forecast.to_dict(orient="records")]
    return PredictResponse(status="ok", last_train=last_train, n_rows=len(records), data=records)

@app.post("/pipeline/load", response_model=LoadResponse, tags=["pipeline"])
async def load(_: None = Depends(verify_secret)):
    """Historise dans RDS les données"""



    #return LoadResponse(status="ok", n_rows=len(records))




@app.post("/data/transfert_log", response_model=LoadResponse, tags=["pipeline"])
async def transfert_log(_: None = Depends(verify_secret)):
    """Historise dans RDS les données"""



# -------------------------------------------------
# Get data from AWS RDS
# -------------------------------------------------     
  
@app.post("/data/processed", response_model=HistoricResponse, tags=["data"])
def get_historic(H: Literal[14, 30], last_train: str):
    """Récupère les datas de la table historic depuis le serveur de base de données AWS RDS"""
    df_historic = get_historic_rds(H, last_train)
    records = [ProcessedRecord(**row) for row in df_historic.to_dict(orient="records")]
    return HistoricResponse(status="ok", n_rows=len(records), horizon=H, last_train=last_train, data=records)

@app.post("/data/forecast", response_model=ForecastResponse, tags=["data"])
def get_forecast(H: Literal[14, 30], last_train):
    """Récupère les datas de la table forecast depuis le serveur de base de données AWS RDS"""
    df_forecast= get_forecast_rds(H, last_train)
    records = [PredictRecord(**row) for row in df_forecast.to_dict(orient="records")]
    return ForecastResponse(status="ok", n_rows=len(records), horizon=H, last_train=last_train, data=records)





'TODO : a revoir'
@app.post("/train", response_model=TrainingResponse, tags=["training"])
def training(H: Literal[14, 30], _: None = Depends(verify_secret)):
    mlflow.set_tracking_uri(mlflow_tracking_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    # Registered name + alias from CONFIG (name is nested by horizon → Prophet)
    name  = CONFIG["mlflow"]["registered_model_name"][f"h{H}"]["Prophet"]
    alias = CONFIG["mlflow"]["model_alias"]          # e.g. "production"

    client = MlflowClient()

    # --- 1. Fetch hyperparams (from @production, fallback to tuning CSV) ---
    PROPHET_FLOAT = {"changepoint_prior_scale", "seasonality_prior_scale",
                     "changepoint_range", "interval_width"}
    PROPHET_BOOL  = {"weekly_seasonality", "daily_seasonality", "yearly_seasonality"}
    PROPHET_STR   = {"seasonality_mode"}
    ALLOWED = PROPHET_FLOAT | PROPHET_BOOL | PROPHET_STR

    # convert to float
    def _cast(k, v):
        if k in PROPHET_FLOAT: return float(v)
        if k in PROPHET_BOOL:  return str(v).lower() == "true"
        return v

    try:
        mv = client.get_model_version_by_alias(name, alias)   # <-- assign it
        prev_version = mv.version
        raw = client.get_run(mv.run_id).data.params
    except RestException:
        logger.warning("No @production for %s — bootstrapping from tuning CSV", name)
        prev_version = None
        best = pd.read_csv(TUNING_CSV_PATH / f"tuning_results_H{H}.csv").iloc[0]
        tuned = {k: str(best[k]) for k in
                 ("changepoint_prior_scale", "seasonality_prior_scale", "changepoint_range")}
        # merge the fixed params so the first model == the tuned config
        # (otherwise weekly/daily_seasonality fall back to Prophet's "auto")
        base = CONFIG["model"]["prophet"]["base_params"]
        raw = {**{k: str(v) for k, v in base.items()}, **tuned}

    params = {k: _cast(k, v) for k, v in raw.items() if k in ALLOWED}

    # --- 2. Dataset (cached S3 read by ETag) ---
    df_prediction = load_cached_dataset()
    daily = build_daily(df_prediction)
    df_train, regressor_cols = build_train_frame(daily, H)

    # --- 3. Fit + log + register + promote ---
    with mlflow.start_run(run_name=f"prophet-production-H{H}") as run:
        mlflow.log_params({**params, "horizon_days": H,
                           "last_train_date": str(df_train["ds"].max().date()),
                           "n_train_rows": len(df_train)})
        mlflow.set_tags({"horizon": str(H), "train_type": "refit"})   # vs "tuning"

        model = Prophet(**params)
        for col in regressor_cols:
            model.add_regressor(col)
        model.fit(df_train)

        info = mlflow.prophet.log_model(
            pr_model=model,
            name="model",                        # artifact_path is deprecated in MLflow 3
            registered_model_name=name,          # <-- CONFIG name
        )
        new_version = str(info.registered_model_version)
        run_id = run.info.run_id

    # --- 4. Promote: same hyperparams, more data -> refit replaces production ---
    #     (champion/challenger comparison is done in prophet_tune.py, where params change)
    promote(client, name, new_version, mv if prev_version else None,
             reason="scheduled refit on new data (same hyperparameters)")

    # --- 5. Swap the API cache (same process: no HTTP needed) ---
    load_model(model="Prophet", horizon=H, force_reload=True)

    return {
        "horizon": H,
        "new_version": new_version,
        "previous_version": str(prev_version) if prev_version else None,
        "run_id": run_id,
    }





