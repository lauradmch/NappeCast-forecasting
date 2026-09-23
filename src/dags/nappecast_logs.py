"""
DAG : nappecast_transfert_log
====================================

BUT DU DAG
----------
Appelle l'endpoint POST /data/transfert_log de l'API NappeCast pour
historiser le fichier de log courant dans S3 avec horodatage.

Déroulé :
    1. transfert_log -> appelle POST /data/transfert_log sur la FastAPI
"""
from __future__ import annotations

import logging
import requests

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.models import Variable

# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — mêmes Variables Airflow que les autres DAGs
# ---------------------------------------------------------------------------
API_BASE_URL    = Variable.get("nappecast_api_base_url", default_var="http://172.31.41.22:8000")
PIPELINE_SECRET = Variable.get("pipeline_secret")
REQUEST_TIMEOUT = 120

# ---------------------------------------------------------------------------
# default_args
# ---------------------------------------------------------------------------
default_args = {
    "owner": "admin",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="nappecast_transfert_log",
    description="Historise le fichier de log NappeCast dans S3 via l'API",
    default_args=default_args,
    schedule="0 * * * *",   # collecte every hour
    start_date=datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    tags=["logs", "s3"],
    doc_md=__doc__,
)


def nappecast_transfert_log():
    @task
    def transfert_log() -> dict:
        """
        Appelle POST /data/transfert_log sur la FastAPI NappeCast.
        L'API uploade logs/nappecast.log dans S3 avec affichage des dates/heures.
        """
        endpoint = f"{API_BASE_URL}/data/transfert_log"
        headers  = {"X-Pipeline-Secret": PIPELINE_SECRET}

        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, headers=headers, timeout=REQUEST_TIMEOUT)

        if response.status_code >= 400:
            logger.error(
                "Réponse API /data/transfert_log (%s) : %s",
                response.status_code,
                response.text
            )

        response.raise_for_status()
        result = response.json()

        logger.info("Transfert log OK : %s", result)
        return result

    transfert_log()

nappecast_transfert_log()