"""
DAG : nappecast_monthly_retrain
================================

BUT DU DAG
----------
Ré-entraîner mensuellement les modèles Prophet de prévision du niveau de nappe,
et ne mettre en production le nouveau modèle que s'il bat celui en place.

Déroulé :
    1a. tune[H=14]   -> déclenche le tuning pour l'horizon 14j
    1b. tune[H=30]   -> idem pour l'horizon 30j
        (1a et 1b sont créées par dynamic task mapping ; le pool
         "training_pool" à 1 slot les sérialise de fait)
    2.  smoke_test   -> vérifie que l'API sert bien une prédiction pour chaque
                        horizon après un éventuel changement de modèle.

Chaque tâche `tune` appelle POST /pipeline/tuning sur l'API NappeCast : le DAG
n'importe pas le code du projet, il ne fait que le déclencher. L'appel est
SYNCHRONE et sans timeout HTTP. Le garde-fou est `execution_timeout` (2h),
pas le client. L'API refuse un second tuning simultané avec un 409.

Côté API, run_tuning(H) :
    - lit le dataset processed depuis S3 (même source que l'API)
    - explore la grille d'hyperparamètres par validation croisée temporelle
    - enregistre une nouvelle version dans le MLflow Model Registry
    - re-score le champion sur les MÊMES données et promeut le challenger
      seulement s'il gagne au moins 2 % (voir src/models/production.py)
    - notifie l'API (/model/reload) si la promotion a eu lieu

Les résultats (métriques, versions, décision de promotion) ne transitent pas
par le DAG : ils sont dans MLflow. La réponse HTTP ne porte qu'un accusé.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from airflow.models import Variable

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# IP privée VPC de l'API (même Variable que le DAG d'ingestion)
API_BASE_URL = Variable.get(
    "nappecast_api_base_url", default_var="http://172.31.41.22:8000"
)

HORIZONS = [14, 30]          # jours — un modèle et une tâche par horizon
REQUEST_TIMEOUT = 120        # s — le chargement d'un modèle MLflow peut être lent

PIPELINE_SECRET = Variable.get("pipeline_secret")
HEADERS = {"X-Pipeline-Secret": PIPELINE_SECRET}

# ---------------------------------------------------------------------------
# default_args : hérités par TOUTES les tasks du DAG
# ---------------------------------------------------------------------------
default_args = {
    "owner": "admin",
    "retries": 0,
}


@dag(
    dag_id="nappecast_monthly_retrain",
    description="Tuning mensuel Prophet + promotion champion/challenger",
    default_args=default_args,
    schedule="0 3 1 * *",              # 1er de chaque mois à 03:00 UTC
    start_date=datetime(2026, 9, 1),
    catchup=False,                     # pas de rattrapage des mois passés
    max_active_runs=1,                 # jamais deux entraînements simultanés
    tags=["nappecast", "training"],
    doc_md=__doc__,
)
def nappecast_monthly_retrain():

    @task(
        execution_timeout=timedelta(hours=2),   # garde-fou : libère le worker
        pool="training_pool",                   # 1 slot -> n'étouffe pas l'ingestion
    )
    def tune(H: int) -> None:
        """
        Tuning complet pour un horizon. Retourne un résumé sérialisable (XCom).
        L'import est dans l'API main.py.
        """
        response = requests.post(
            f"{API_BASE_URL}/pipeline/tuning",
            params={"H": H},
            timeout=None,
            headers=HEADERS,
        )
        response.raise_for_status()


    @task
    def smoke_test() -> None:
        """
        Dernière barrière avant que le modèle serve en production : on vérifie
        que l'API répond bien à une prédiction pour chaque horizon.
        Un échec ici fait échouer le DAG et rend le problème visible
        (le rollback se fait avec : python -m src.models.production --rollback).
        """
        for H in HORIZONS:
            response = requests.post(
                f"{API_BASE_URL}/pipeline/forecast",
                params={"H": H},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            print(f"H={H}d | predict OK ({payload['n_rows']} points)")

    # .expand() = dynamic task mapping : Airflow crée une instance de `tune`
    # par valeur de HORIZONS, exécutées en parallèle. smoke_test reçoit la
    # liste des dicts retournés.
    tune.expand(H=HORIZONS) >> smoke_test()


nappecast_monthly_retrain()