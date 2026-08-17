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
from src.config import load_config
from src.data.make_dataset import build_dataset
from src.data.feat_dataset import feat_dataset
from src.helper.aws import upload_file_to_s3, read_csv_in_s3

from src.api.model_loader import get_model_info, load_model, _MLFLOW_LOADERS
from src.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictResponse,
    TrainingResponse,
)
from src.models.prophet import (build_train_frame,
                                build_future_frame,
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

EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "prophet-groundwater-tuning")

logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
logger = logging.getLogger(__name__)

PIPELINE_SECRET = os.environ["PIPELINE_SECRET"]

_cache: dict = {}  # {"etag": str, "df": pd.DataFrame}

#--------------------- ENDPOINTS & HELPERS ---------------------
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


@app.get("/data/preview", tags=["monitoring"])
def get_data(n: int = 50):
    """Read-only data preview of the most recent 'n' rows (default 50)"""
    df = load_cached_dataset()
    out = df.tail(n).copy()
    out["date_index"] = pd.to_datetime(out["date_index"]).dt.strftime("%Y-%m-%d")
    return out.to_dict(orient="records")

@app.post("/pipeline/collect")
async def collect_pipeline(_: None = Depends(verify_secret)):
    print("Fetching Data")
    df_station, df_interim = build_dataset(skip_historical=True, save_csv=True)
    df_processed = feat_dataset(save_csv=True)
    return {"status": "ok", "stations": len(df_station), "processed_rows": len(df_processed)}


@app.get("/model/info", response_model=ModelInfoResponse, tags=["monitoring"])
def model_info(model: Optional[str] = None, source: Optional[str] = None, horizon: Optional[int] = None):
    """État du modèle en cache pour le type/source donnés (ou le modèle actif par défaut si omis)."""
    return get_model_info(model=model, source=source, horizon=horizon)


@app.post("/model/reload", response_model=ModelInfoResponse, tags=["monitoring"])
def model_reload(model: Optional[str] = None, source: Optional[str] = None, horizon: Optional[int] = None):
    """Force un rechargement du modèle (type/source donnés, ou modèle actif par défaut) — utile après un nouvel entraînement."""
    try:
        load_model(model=model, source=source, horizon=horizon, force_reload=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec du rechargement du modèle : {e}")
    return get_model_info(model=model, source=source, horizon=horizon)


@app.get("/model/info/all", response_model=Dict[str, ModelInfoResponse], tags=["monitoring"])
def model_info_all(source: Optional[str] = None, horizon: Optional[int] = None):
    """
    État des modèles en une seule requête.
    """
    return {
        f"{model_type}_h{H}": get_model_info(model=model_type, source=source, horizon=H)
        for H in (14, 30)
        for model_type in _MLFLOW_LOADERS.keys()
}


def load_cached_dataset() -> pd.DataFrame:
    head = S3_SESSION.head_object(Bucket=BUCKET_NAME, Key=PROCESSED_FILENAME)
    etag = head["ETag"]
    if _cache.get("etag") != etag:
        logger.info("Dataset cache miss (etag=%s) — reloading from S3", etag)
        _cache["df"]   = read_csv_in_s3(S3_SESSION, BUCKET_NAME, PROCESSED_FILENAME)
        _cache["etag"] = etag
    return _cache["df"]


@app.post("/train", response_model=TrainingResponse, tags=["training"])
def training(H: Literal[14, 30], _: None = Depends(verify_secret)):
    if "MLFLOW_TRACKING_URI" in os.environ:
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
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
        raw = {k: str(best[k]) for k in
               ("changepoint_prior_scale", "seasonality_prior_scale", "changepoint_range")}
        # merge in BASE_PARAMS so the first run has the full config too
        #raw = {**{k: str(v) for k, v in BASE_PARAMS.items()}, **raw}

    params = {k: _cast(k, v) for k, v in raw.items() if k in ALLOWED}

    # --- 2. Dataset (cached S3 read by ETag) ---
    df_prediction = load_cached_dataset()
    daily = build_daily(df_prediction)
    df_train, regressor_cols = build_train_frame(daily, H)

    # --- 3. Fit + log + register + promote ---
    with mlflow.start_run(run_name=f"prophet-production-H{H}") as run:
        mlflow.log_params({**params, "horizon_days": H})
        mlflow.set_tag("horizon", str(H))

        model = Prophet(**params)
        for col in regressor_cols:
            model.add_regressor(col)
        model.fit(df_train)

        info = mlflow.prophet.log_model(
            pr_model=model,
            artifact_path="model",
            registered_model_name=name,          # <-- CONFIG name
        )
        new_version = info.registered_model_version
        client.set_registered_model_alias(name, alias, new_version)
        run_id = run.info.run_id

    # --- 4. Swap the API cache ---
    load_model(model="Prophet", horizon=H, force_reload=True)

    return {
        "horizon": H,
        "new_version": str(new_version),
        "previous_version": str(prev_version) if prev_version else None,
        "run_id": run_id,
    }


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
def predict(H: Literal[14, 30]):
    # build future dataframe
    df = load_cached_dataset()
    daily = build_daily(df)
    future, _ = build_future_frame(daily, H)

    # load model in prod
    try:
        model = load_model(model='Prophet', horizon=H)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {e}")

    # forecast
    try:
        forecast = model.predict(future)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Prediction failed: {e}")

    last_train = daily[daily[TARGET].notna()].index.max().strftime("%Y-%m-%d")
    forecast["ds"] = forecast["ds"].dt.strftime("%Y-%m-%d")
    # converts forcast df to a list of dicts, one dict (day) per row 
    points = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_dict(orient="records")

    return {"last_train": last_train, "points": points}