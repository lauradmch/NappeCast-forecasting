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
from typing import Dict
from src.config import load_config
from src.data.make_dataset import build_dataset
from src.api.model_loader import get_model_info, load_model
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

CONFIG = load_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Remplace l'ancien @app.on_event("startup") (déprécié). Le code avant
    le `yield` s'exécute au démarrage, celui après à l'arrêt -- ici on
    n'a besoin que du démarrage.
    """
    try:
        load_model()
    except Exception as e:
        logger.warning("Préchargement du modèle échoué au démarrage : %s", e)

    yield  # l'API tourne ici -- rien à faire à l'arrêt pour ce projet


app = FastAPI(
    title="NappCast",
    description="Sert les prédictions du modèle entraîné (source configurable : local, S3, MLflow).",
    version="1.0.0"
)

def _predict(df: pd.DataFrame):
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

@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
def health():
    """
    Vérifie que l'API répond — ne garantit pas que le modèle est chargé (voir /model/info).
    """
    return {"status": "ok"}


@app.get("/data")
async def get_data():
    print("Fetching Data")
    df_station, df_processed = build_dataset(skip_historical=True)

    response = {
        "stations": df_station.to_json(orient="split"),
        "processed": df_processed.to_json(orient="split")
    }
    return response


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


@app.get("/compare")
async def compare_models():
    df_station, df_processed = build_dataset(skip_historical=True)

    now = pd.Timestamp.now()
    month_end = now.to_period("M").end_time.normalize()

    results = {}
    for model_type in CONFIG["mlflow"]["registered_model_name"].keys():
        try:
            model = load_model(model=model_type, source="mlflow")

            if model_type == "Prophet":
                # génération du jeu de predict
                days_to_month_end = (month_end - now).days + 1
                future = model.make_future_dataframe(periods=days_to_month_end)
                forecast = model.predict(future)

                # valeur prédite pour la fin du mois en cours
                row = forecast[forecast["ds"] == month_end]
                value = float(row["yhat"].iloc[0]) if not row.empty else float(forecast["yhat"].iloc[-1])
                results[model_type] = {"date": str(month_end.date()), "prediction": value}

            else:
                # a voir ici
                pred = model.predict(df_processed.tail(1))
                results[model_type] = {"date": str(month_end.date()), "prediction": float(pred[0])}

        except Exception as e:
            logger.error("Erreur pour %s : %s", model_type, e)
            results[model_type] = {"error": str(e)}

    return results


@app.get("/model/info/all", response_model=Dict[str, ModelInfoResponse], tags=["monitoring"])
def model_info_all(source: Optional[str] = None):
    """État des 3 modèles (LinearRegression, XGBoost, Prophet) en une seule requête."""
    return {
        model_type: get_model_info(model=model_type, source=source)
        for model_type in CONFIG["mlflow"]["registered_model_name"].keys()
    }