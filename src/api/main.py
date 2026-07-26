"""
API de test (acces databse, acces inférence ...)
"""

import uvicorn
import pandas as pd 
import boto3
import urllib 
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.schemas import (
    BatchObservations,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    Observation,
    PredictionResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NappCast",
    description="Sert les prédictions du modèle entraîné (source configurable : local, S3, MLflow).",
    version="1.0.0"
)

@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
def health():
    """Vérifie que l'API répond — ne garantit pas que le modèle est chargé (voir /model/info)."""
    return {"status": "ok"}
