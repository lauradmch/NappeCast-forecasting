"""
DAG : nappecast_monthly_retrain
================================

BUT DU DAG
----------
Ré-entraîner mensuellement les modèles Prophet de prévision du niveau de nappe,
et ne mettre en production le nouveau modèle que s'il bat celui en place.

Déroulé :
    1a. tune[H=14]   -> grid search + refit + champion/challenger pour l'horizon 14j
    1b. tune[H=30]   -> idem pour l'horizon 30j
        (1a et 1b tournent en PARALLÈLE via dynamic task mapping)
    2.  smoke_test   -> vérifie que l'API sert bien une prédiction pour chaque
                        horizon après un éventuel changement de modèle.

Chaque tâche `tune` appelle src.models.prophet_tune.run_tuning(H), qui :
    - lit le dataset processed depuis S3 (même source que l'API : pas de skew)
    - explore la grille d'hyperparamètres par validation croisée temporelle
    - enregistre une nouvelle version dans le MLflow Model Registry
    - re-score le champion sur les MÊMES données et promeut le challenger
      seulement s'il gagne au moins 2 % (voir src/models/production.py)
    - notifie l'API (/model/reload) si la promotion a eu lieu
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
    def tune(H: int) -> dict:
        """
        Tuning complet pour un horizon. Retourne un résumé sérialisable (XCom).

        L'import est LOCAL et non en tête de fichier : le scheduler reparse tous
        les DAGs toutes les 30 s, ici l'import n'a lieu que dans le worker.
        """
        from src.models.prophet_tune import run_tuning

        return run_tuning(H, source="s3")

    @task
    def smoke_test(results: list[dict]) -> None:
        """
        Dernière barrière avant que le modèle serve en production : on vérifie
        que l'API répond bien à une prédiction pour chaque horizon.
        Un échec ici fait échouer le DAG et rend le problème visible
        (le rollback se fait avec : python -m src.models.production --rollback).
        """
        for r in results:
            response = requests.post(
                f"{API_BASE_URL}/predict",
                params={"H": r["horizon"]},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            print(
                f"H={r['horizon']}d | promoted={r['promoted']} "
                f"| version={r['version']} | predict OK ({payload['n_rows']} points)"
            )

    # .expand() = dynamic task mapping : Airflow crée une instance de `tune`
    # par valeur de HORIZONS, exécutées en parallèle. smoke_test reçoit la
    # liste des dicts retournés.
    smoke_test(tune.expand(H=HORIZONS))


nappecast_monthly_retrain()