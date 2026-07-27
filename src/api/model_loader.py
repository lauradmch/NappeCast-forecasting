"""
Chargement du modèle servi par l'API, depuis l'une de 2 sources
(configs/config.yaml, section api.model_source) :
- "local"  : models/<model_filename>, pour le développement
- "mlflow" : registre de modèles MLflow (api.mlflow)
Le modèle chargé est mis en cache en mémoire (process API), pour ne pas
le retélécharger à chaque requête. /model/reload force un rechargement.
"""

import logging
import os
import tempfile
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.prophet

from pathlib import Path
from typing import Any, Optional, Dict
from src.config import load_config

logger = logging.getLogger(__name__)

CONFIG = load_config()

_MLFLOW_LOADERS = {
    "LinearRegression": mlflow.sklearn.load_model,
    "XGBoost": mlflow.sklearn.load_model,
    "Prophet": mlflow.prophet.load_model,
}

_MODELS = {
    "Linear": CONFIG["mlflow"]["registered_model_name"]["LinearRegression"],
    "XGBoost": CONFIG["mlflow"]["registered_model_name"]["XGBoost"],
}

_cache: dict = {}  # clé : (source, model_type)

def _load_from_local() -> Any:
    model_path = Path(CONFIG["paths"]["models"]) / CONFIG["paths"]["model_filename"]
    if not model_path.exists():
        raise FileNotFoundError(f"{model_path} introuvable.")
    return joblib.load(model_path)


def _load_from_mlflow(model: Optional[str] = None) -> Any:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI") or CONFIG["mlflow"]["default_tracking_uri"]
    mlflow.set_tracking_uri(tracking_uri)

    model_type = model or CONFIG["mlflow"].get("active_model", "XGBoost")

    if model_type not in _MLFLOW_LOADERS:
        raise ValueError(f"Type de modèle inconnu : {model_type!r} (attendu {list(_MLFLOW_LOADERS)})")

    registered_name = CONFIG["mlflow"]["registered_model_name"][model_type]
    alias = CONFIG["mlflow"]["model_alias"]
    model_uri = f"models:/{registered_name}@{alias}"

    loaded_model = _MLFLOW_LOADERS[model_type](model_uri)
    logger.info("Modèle chargé depuis MLflow : %s (type=%s)", model_uri, model_type)
    return loaded_model


def load_model(model: Optional[str] = None, source: Optional[str] = None, force_reload: bool = False) -> Any:
    source = source or CONFIG["api"]["model_source"]
    model_type = model or CONFIG["mlflow"].get("active_model", "XGBoost")
    cache_key = (source, model_type)

    cached = _cache.get(cache_key)
    if cached and cached.get("model") is not None and not force_reload:
        return cached["model"]

    if source not in _LOADERS:
        raise ValueError(f"model_source inconnu : {source!r} (attendu 'local' ou 'mlflow')")

    logger.info("Chargement du modèle (source=%s, type=%s)...", source, model_type)
    try:
        loaded = _LOADERS[source](model_type)
    except Exception as e:
        _cache[cache_key] = {
            "model": cached.get("model") if cached else None,
            "loaded_at": cached.get("loaded_at") if cached else None,
            "detail": str(e),
        }
        raise

    _cache[cache_key] = {
        "model": loaded,
        "loaded_at": pd.Timestamp.now().isoformat(),
        "detail": None,
    }
    return loaded


def get_model_info(model: Optional[str] = None, source: Optional[str] = None) -> dict:
    source = source or CONFIG["api"]["model_source"]
    model_type = model or CONFIG["mlflow"].get("active_model", "XGBoost")
    cache_key = (source, model_type)

    entry = _cache.get(cache_key, {})

    return {
        "loaded": entry.get("model") is not None,
        "source": source,
        "model_type": model_type,
        "loaded_at": entry.get("loaded_at"),
        "detail": entry.get("detail"),
    }