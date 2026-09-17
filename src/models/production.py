"""
Champion / challenger promotion in the MLflow Model Registry.

Vocabulary
----------
* Registered model : named, versioned entry in the registry
                     (e.g. "nappecast_Prophet_h14" -> v1, v2, v3...).
* Alias            : a movable label pointing to ONE version
                     (e.g. "production" -> v3). The API loads
                     "models:/<name>@production", so moving the alias
                     changes the served model without touching the API code.
* Champion         : the version currently holding the production alias.
* Challenger       : the freshly tuned version, candidate for production.

Decision rule
-------------
Lower score is better (score = select_score = penalized CV RMSE).
The challenger is promoted only if it beats the champion by at least
MIN_RELATIVE_GAIN (avoids swapping models for noise-level differences).

For a fair comparison, both models must be scored on the SAME data and the
SAME CV folds. The champion's stored score was computed on older data, so the
caller can pass `rescore_champion`, a function that re-runs the CV of the
champion's hyperparameters on today's data.

CLI (run from the project root)
-------------------------------
    python -m src.models.production --horizon 14 --status
    python -m src.models.production --horizon 14 --promote 7
    python -m src.models.production --horizon 14 --rollback
"""
import os
import requests
import argparse
import logging
from typing import Callable, Optional

import mlflow
from mlflow import MlflowClient
from mlflow.entities.model_registry import ModelVersion
from mlflow.exceptions import MlflowException

from src.config import load_config

logger = logging.getLogger(__name__)

CONFIG = load_config()
API_URL = os.getenv("API_URL")

PRODUCTION_ALIAS = CONFIG["mlflow"]["model_alias"]    # "production" (read by the API)
CHALLENGER_ALIAS = "challenger"
PREVIOUS_ALIAS   = "previous_production"               # kept for 1-command rollback
SCORE_METRIC     = "select_score"                      # lower is better
MIN_RELATIVE_GAIN = 0.02                               # challenger must be >= 2 % better


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def registered_name(H: int, model_type: str = "Prophet") -> str:
    """Same lookup as src/api/model_loader.py -> training and serving agree."""
    return CONFIG["mlflow"]["registered_model_name"][f"h{H}"][model_type]


def get_version_by_alias(client: MlflowClient, name: str, alias: str) -> Optional[ModelVersion]:
    """Return the version behind `alias`, or None if the alias does not exist yet."""
    try:
        return client.get_model_version_by_alias(name, alias)
    except MlflowException:
        # Raised when the alias (or the registered model) doesn't exist, e.g. first run
        return None


def get_run_metric(client: MlflowClient, mv: ModelVersion, metric: str) -> Optional[float]:
    """Read a metric from the training run that produced a model version."""
    return client.get_run(mv.run_id).data.metrics.get(metric)


def get_run_params(client: MlflowClient, mv: ModelVersion) -> dict:
    """Params logged in that run (MLflow stores them as strings)."""
    return client.get_run(mv.run_id).data.params


def promote(client: MlflowClient, name: str, new_version: str,
             old: Optional[ModelVersion], reason: str) -> None:
    """Move the production alias; keep the old champion reachable for rollback."""
    if old is not None:
        client.set_registered_model_alias(name, PREVIOUS_ALIAS, old.version)
    client.set_registered_model_alias(name, PRODUCTION_ALIAS, new_version)
    client.set_model_version_tag(name, new_version, "promotion_reason", reason)
    logger.info("%s v%s -> @%s (%s)", name, new_version, PRODUCTION_ALIAS, reason)

API_URL = os.getenv("API_URL", "").rstrip("/")   # e.g. http://<ec2-ip>:8000, in .env

def notify_api_reload(H: int, model_type: str = "Prophet") -> None:
    """Tell the API to drop its cached model and reload @production."""
    if not API_URL:
        logger.warning("API_URL not set: API not notified, call /model/reload manually")
        return
    try:
        r = requests.post(f"{API_URL}/model/reload",
                          params={"model": model_type, "horizon": H},
                          headers={"X-Pipeline-Secret": os.getenv("PIPELINE_SECRET", "")},
                          timeout=120)   # downloading from MLflow/S3 can be slow
        r.raise_for_status()
        logger.info("API reloaded H=%d: %s", H, r.json())
    except requests.RequestException as e:
        # The promotion already happened in the registry: don't crash, just warn
        logger.warning("API reload failed (H=%d): %s", H, e)

# ---------------------------------------------------------------------------
# Main entry point used by prophet_tune.py
# ---------------------------------------------------------------------------
def promote_if_better(
    name: str,
    challenger_version: str,
    challenger_score: float,
    rescore_champion: Optional[Callable[[dict], float]] = None,
    min_relative_gain: float = MIN_RELATIVE_GAIN,
) -> dict:
    """
    Compare challenger vs current champion and move the production alias if needed.

    Parameters
    ----------
    name               : registered model name (e.g. "nappecast_Prophet_h14")
    challenger_version : version number of the freshly registered model
    challenger_score   : its select_score on the current data (lower = better)
    rescore_champion   : optional f(champion_run_params) -> score on current data.
                         If None, the champion's stored metric is used (less fair).
    min_relative_gain  : minimal relative improvement required to promote

    Returns a dict describing the decision (logged by the caller).
    """
    client = MlflowClient()
    challenger_version = str(challenger_version)

    # 1. Tag the new version as challenger
    client.set_registered_model_alias(name, CHALLENGER_ALIAS, challenger_version)

    champion = get_version_by_alias(client, name, PRODUCTION_ALIAS)

    # 2. No champion yet -> first model goes straight to production
    if champion is None:
        promote(client, name, challenger_version, None, "first production model")
        return {"promoted": True, "champion_version": None,
                "champion_score": None, "challenger_score": challenger_score}

    # 3. Same version (re-run without new registration) -> nothing to do
    if str(champion.version) == challenger_version:
        return {"promoted": False, "champion_version": champion.version,
                "champion_score": challenger_score, "challenger_score": challenger_score}

    # 4. Score the champion (fair: re-evaluated on today's data; fallback: stored metric)
    if rescore_champion is not None:
        champion_score = rescore_champion(get_run_params(client, champion))
        score_source = "rescored on current data"
    else:
        champion_score = get_run_metric(client, champion, SCORE_METRIC)
        score_source = "stored metric"

    if champion_score is None:
        # Old champion logged without select_score -> can't compare, promote and say why
        promote(client, name, challenger_version, champion,
                 f"champion v{champion.version} has no {SCORE_METRIC}")
        return {"promoted": True, "champion_version": champion.version,
                "champion_score": None, "challenger_score": challenger_score}

    # 5. Decision: lower is better, with a minimum relative gain
    threshold = champion_score * (1 - min_relative_gain)
    promoted = challenger_score < threshold

    logger.info("[%s] champion v%s score=%.4f (%s) | challenger v%s score=%.4f | threshold=%.4f -> %s",
                name, champion.version, champion_score, score_source,
                challenger_version, challenger_score, threshold,
                "PROMOTE" if promoted else "KEEP CHAMPION")

    client.set_model_version_tag(name, challenger_version, "compared_to", f"v{champion.version}")
    client.set_model_version_tag(name, challenger_version, "champion_score", f"{champion_score:.4f}")

    if promoted:
        gain = 1 - challenger_score / champion_score
        promote(client, name, challenger_version, champion,
                 f"beats v{champion.version} by {gain:.1%} ({score_source})")

    return {"promoted": promoted, "champion_version": champion.version,
            "champion_score": champion_score, "challenger_score": challenger_score}


# ---------------------------------------------------------------------------
# Manual operations (CLI)
# ---------------------------------------------------------------------------
def rollback(name: str) -> None:
    """Put the previous production version back in production."""
    client = MlflowClient()
    previous = get_version_by_alias(client, name, PREVIOUS_ALIAS)
    current = get_version_by_alias(client, name, PRODUCTION_ALIAS)
    if previous is None:
        raise RuntimeError(f"No @{PREVIOUS_ALIAS} for {name}: nothing to roll back to.")
    client.set_registered_model_alias(name, PRODUCTION_ALIAS, previous.version)
    if current is not None:
        client.set_registered_model_alias(name, PREVIOUS_ALIAS, current.version)
    logger.info("Rollback %s: @%s -> v%s", name, PRODUCTION_ALIAS, previous.version)


def status(name: str) -> None:
    client = MlflowClient()
    for alias in (PRODUCTION_ALIAS, CHALLENGER_ALIAS, PREVIOUS_ALIAS):
        mv = get_version_by_alias(client, name, alias)
        if mv is None:
            print(f"@{alias:<20} -")
        else:
            score = get_run_metric(client, mv, SCORE_METRIC)
            print(f"@{alias:<20} v{mv.version}  {SCORE_METRIC}={score}  run={mv.run_id}")


def main():
    logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
    parser = argparse.ArgumentParser(description="Manage the production alias in MLflow.")
    parser.add_argument("--horizon", type=int, required=True, choices=[14, 30])
    parser.add_argument("--model-type", default=CONFIG["mlflow"]["active_model"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="show aliases")
    group.add_argument("--promote", metavar="VERSION", help="force a version to production")
    group.add_argument("--rollback", action="store_true", help="restore previous production")
    args = parser.parse_args()

    # MLFLOW_TRACKING_URI comes from .env (loaded by src.config)
    name = registered_name(args.horizon, args.model_type)

    if args.status:
        status(name)
    elif args.promote:
        client = MlflowClient()
        old = get_version_by_alias(client, name, PRODUCTION_ALIAS)
        promote(client, name, args.promote, old, "manual promotion")
        notify_api_reload(args.horizon)
    elif args.rollback:
        rollback(name)
        notify_api_reload(args.horizon)


if __name__ == "__main__":
    main()
