"""
API de test (acces databse, acces inférence ...)
"""

import uvicorn
import pandas as pd 
import boto3
import urllib 
import logging
import os

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from typing import Dict, Optional
from src.config import load_config
from src.data.make_dataset import build_dataset
from src.data.feat_dataset import feat_dataset
from src.helper.aws import upload_file_to_s3

from src.api.model_loader import get_model_info, load_model
from src.api.schemas import (
    BatchObservations,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    Observation,
    PredictionResponse,
)

CONFIG = load_config()

logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
logger = logging.getLogger(__name__)

PIPELINE_SECRET = os.environ["PIPELINE_SECRET"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_model()
    except Exception as e:
        logger.warning("Préchargement du modèle échoué au démarrage : %s", e)

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


@app.get("/data")
async def get_data():
    print("Fetching Data")
    df_station, df_interim = build_dataset(skip_historical=True, save_csv=True)
    df_processed = feat_dataset(save_csv=True)

    response = {
        "stations": df_station.to_json(orient="split"),
        "processed": df_processed.to_json(orient="split")
    }
    return response

@app.post("/pipeline/collect")
async def collect_pipeline(_: None = Depends(verify_secret)):
    print("Fetching Data")
    df_station, df_interim = build_dataset(skip_historical=True, save_csv=True)
    df_processed = feat_dataset(save_csv=True)
    return {"status": "ok", "stations": len(df_station), "processed_rows": len(df_processed)}


@app.get("/model/info", response_model=ModelInfoResponse, tags=["monitoring"])
def model_info(model: Optional[str] = None, source: Optional[str] = None):
    """État du modèle en cache pour le type/source donnés (ou le modèle actif par défaut si omis)."""
    return get_model_info(model=model, source=source)


@app.post("/model/reload", response_model=ModelInfoResponse, tags=["monitoring"])
def model_reload(model: Optional[str] = None, source: Optional[str] = None):
    """Force un rechargement du modèle (type/source donnés, ou modèle actif par défaut) — utile après un nouvel entraînement."""
    try:
        load_model(model=model, source=source, force_reload=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec du rechargement du modèle : {e}")
    return get_model_info(model=model, source=source)


@app.get("/model/info/all", response_model=Dict[str, ModelInfoResponse], tags=["monitoring"])
def model_info_all(source: Optional[str] = None):
    """
    État des modèles en une seule requête.
    """
    
    return {
        model_type: get_model_info(model=model_type, source=source)
        for model_type in CONFIG["mlflow"]["registered_model_name"].keys()
    }



def _predict(df: pd.DataFrame, H: int):
    try:

        model = load_model()


    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Modèle indisponible : {e}")

    try:
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)[:, 1]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur lors de la prédiction : {e}")

    return predictions, probabilities



@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
def predict(observation: Observation):
    """Prédiction sur une observation unique. La météo de la région est récupérée automatiquement."""


    enriched = _enrich_with_weather(observation)



    df = pd.DataFrame([enriched])
    predictions, probabilities = _predict(df)
    return {"prediction": int(predictions[0]), "probabilite": float(probabilities[0])}