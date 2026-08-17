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
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.prophet

from pathlib import Path
from typing import Any, Optional
from src.config import load_config

logger = logging.getLogger(__name__)

CONFIG = load_config()

# Dispatch du flavor MLflow selon le type de modèle
_MLFLOW_LOADERS = {
    "Prophet": mlflow.prophet.load_model,
}

_cache: dict = {}  # clé : (source, model_type, horizon)

def _horizon_key(horizon: int) -> str:
    """14 → 'h14', 30 → 'h30'. Raises for anything else."""
    if horizon not in (14, 30):
        raise ValueError(f"Unsupported horizon: {horizon!r}. Expected one of {[14, 30]}.")
    return f"h{horizon}"

def _load_from_local(model: Optional[str] = None, horizon: Optional[int] = None) -> Any:
    # horizon ignored: local dev has one file per model type, no per-horizon variant
    model_type = model or CONFIG["mlflow"]["active_model"]
    filename = CONFIG["paths"]["local_model_filenames"][model_type]
    model_path = Path(CONFIG["paths"]["models"]) / filename

    if not model_path.exists():
        raise FileNotFoundError(f"{model_path} introuvable.")
    return joblib.load(model_path)


def _load_from_mlflow(model: Optional[str] = None, horizon: Optional[int] = None) -> Any:
    tracking_uri = CONFIG["mlflow"]["internal_tracking_uri"]
    mlflow.set_tracking_uri(tracking_uri)

    model_type = model or CONFIG["mlflow"]["active_model"]
    h_key = _horizon_key(horizon)

    if model_type not in _MLFLOW_LOADERS:
        raise ValueError(f"Unknown model type : {model_type!r} (expecting {list(_MLFLOW_LOADERS)})")
    
    registered_name = CONFIG["mlflow"]["registered_model_name"][h_key][model_type]

    alias = CONFIG["mlflow"]["model_alias"]
    model_uri = f"models:/{registered_name}@{alias}"

    loaded_model = _MLFLOW_LOADERS[model_type](model_uri)
    logger.info("Modèle chargé depuis MLflow : %s (type=%s)", model_uri, model_type)
    return loaded_model


_LOADERS = {
    "local": _load_from_local,
    "mlflow": _load_from_mlflow,
}


def load_model(model: Optional[str] = None, source: Optional[str] = None, force_reload: bool = False, horizon: Optional[int] = None) -> Any:
    source = source or CONFIG["api"]["model_source"]
    model_type = model or CONFIG["mlflow"]["active_model"]
    cache_key = (source, model_type, horizon)

    cached = _cache.get(cache_key)
    if cached and cached.get("model") is not None and not force_reload:
        return cached["model"]

    if source not in _LOADERS:
        raise ValueError(f"model_source inconnu : {source!r} (attendu 'local' ou 'mlflow')")

    logger.info("Chargement du modèle (source=%s, type=%s)...", source, model_type)
    try:
        loaded = _LOADERS[source](model_type, horizon)
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


def get_model_info(model: Optional[str] = None, source: Optional[str] = None, horizon: Optional[int] = None) -> dict:
    source = source or CONFIG["api"]["model_source"]
    model_type = model or CONFIG["mlflow"]["active_model"]
    cache_key = (source, model_type, horizon)

    entry = _cache.get(cache_key, {})

    return {
        "loaded": entry.get("model") is not None,
        "source": source,
        "horizon": horizon,
        "model_type": model_type,
        "loaded_at": entry.get("loaded_at"),
        "detail": entry.get("detail"),
    }