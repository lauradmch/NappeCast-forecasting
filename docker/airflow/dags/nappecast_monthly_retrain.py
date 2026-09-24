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
         "training_pool" à 1 slot les exécute l'une après l'autre)
    2.  smoke_test   -> vérifie que l'API sert bien une prédiction pour chaque
                        horizon après un éventuel changement de modèle.

Chaque tâche `tune` appelle POST /pipeline/tuning sur l'API NappeCast : le DAG
n'importe pas le code du projet, il ne fait que le déclencher. L'appel est
SYNCHRONE :
    - timeout de connexion court (API injoignable -> échec en quelques secondes)
    - timeout de lecture long, juste sous `execution_timeout` (2h)
L'API refuse un second tuning simultané avec un 409 : la tâche échoue alors
avec un message explicite (un tuning précédent tourne encore côté API).

Côté API, run_tuning(H) :
    - lit le dataset processed depuis S3 (même source que l'API)
    - explore la grille d'hyperparamètres par validation croisée temporelle
    - enregistre une nouvelle version dans le MLflow Model Registry
    - re-score le champion sur les MÊMES données et promeut le challenger
      seulement s'il gagne au moins 2 % (voir src/models/production.py)
    - notifie l'API (/model/reload) si la promotion a eu lieu

Les résultats (métriques, versions, décision de promotion) ne transitent pas
par le DAG : ils sont dans MLflow. La réponse HTTP ne porte qu'un accusé.

PRÉREQUIS
---------
    - Variables Airflow : `pipeline_secret` (obligatoire),
      `nappecast_api_base_url` (optionnelle)
    - Pool `training_pool` avec 1 slot :
        airflow pools set training_pool 1 "Serialise les tunings NappeCast"
"""

from __future__ import annotations

from datetime import datetime, timedelta

import requests
from airflow.sdk import Variable, dag, task

# ---------------------------------------------------------------------------
# Configuration (constantes uniquement : aucune lecture de Variable ici,
# ce code est exécuté à chaque parsing du DAG)
# ---------------------------------------------------------------------------
DEFAULT_API_BASE_URL = "http://172.31.41.22:8000"   # IP privée VPC de l'API

HORIZONS = [14, 30]                 # jours — un modèle et une tâche par horizon

TUNE_EXECUTION_TIMEOUT = timedelta(hours=2)
CONNECT_TIMEOUT = 10                # s — API injoignable => échec rapide
TUNE_READ_TIMEOUT = 7000            # s — juste sous execution_timeout (7200 s)
SMOKE_TIMEOUT = (CONNECT_TIMEOUT, 120)  # le chargement d'un modèle MLflow peut être lent


def _api_config() -> tuple[str, dict[str, str]]:
    """Lit la configuration au runtime (et non au parsing du DAG)."""
    base_url = Variable.get("nappecast_api_base_url", default=DEFAULT_API_BASE_URL)
    headers = {"X-Pipeline-Secret": Variable.get("pipeline_secret")}
    return base_url.rstrip("/"), headers


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
    # Garde-fou global : 2 tunings x 2h + smoke test. Au-delà, le run est
    # marqué failed et ne bloque plus les runs suivants (restés en "queued").
    dagrun_timeout=timedelta(hours=5),
    tags=["nappecast", "training"],
    doc_md=__doc__,
)
def nappecast_monthly_retrain():

    @task(
        execution_timeout=TUNE_EXECUTION_TIMEOUT,  # garde-fou : libère le worker
        pool="training_pool",                      # 1 slot -> n'étouffe pas l'ingestion
    )
    def tune(H: int) -> None:
        """Déclenche le tuning complet pour un horizon (résultats dans MLflow)."""
        base_url, headers = _api_config()

        response = requests.post(
            f"{base_url}/pipeline/tuning",
            params={"H": H},
            headers=headers,
            timeout=(CONNECT_TIMEOUT, TUNE_READ_TIMEOUT),
        )

        if response.status_code == 409:
            raise RuntimeError(
                f"H={H}d : un tuning est déjà en cours côté API (409). "
                "Attendre sa fin (logs API / MLflow) puis faire un Clear de la tâche."
            )
        response.raise_for_status()
        print(f"H={H}d | tuning terminé : {response.text[:500]}")

    @task
    def smoke_test() -> None:
        """
        Dernière barrière avant que le modèle serve en production : on vérifie
        que l'API répond bien à une prédiction pour chaque horizon.
        Un échec ici fait échouer le DAG et rend le problème visible
        (le rollback se fait avec : python -m src.models.production --rollback).
        """
        base_url, headers = _api_config()

        for H in HORIZONS:
            response = requests.post(
                f"{base_url}/pipeline/forecast",
                params={"H": H},
                headers=headers,
                timeout=SMOKE_TIMEOUT,
            )
            response.raise_for_status()
            n_rows = response.json().get("n_rows")
            if not n_rows:
                raise ValueError(f"H={H}d : prédiction vide ou réponse inattendue")
            print(f"H={H}d | predict OK ({n_rows} points)")

    # .expand() = dynamic task mapping : une instance de `tune` par horizon.
    # Le pool à 1 slot les exécute l'une après l'autre ; smoke_test ne démarre
    # que si les deux ont réussi.
    tune.expand(H=HORIZONS) >> smoke_test()


nappecast_monthly_retrain()