"""
DAG : nappecast_fetch_external_apis
====================================

BUT DU DAG
----------
Déclencher, via l'API NappeCast (172.31.41.22:8000), la récupération des
données provenant des APIs externes Hibeau et OpenWeather.

Déroulé :
    1a. check_hubeau_health         -> teste directement l'API Hubeau.
    1b. check_openweather_health    -> teste directement l'API OpenWeather.
        (1a et 1b tournent en PARALLÈLE)
    2.  health_checks_passed        -> tâche de JONCTION (vide pour l'instant),
        qui attend que 1a ET 1b aient réussi avant de continuer.
    3   fetch_data                  -> déclenche la récupération des datas.

"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator

# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = Variable.get(
    "nappecast_api_base_url", default_var="http://172.31.41.22:8000"
)

HUBEAU_BASE_URL = Variable.get(
    "hubeau_base_url", default_var="https://hubeau.eaufrance.fr/api/v1/niveaux_nappes"
)

OPEN_METEO_BASE_URL = Variable.get(
    "open_meteo_base_url", default_var="https://archive-api.open-meteo.com/v1"
)

REQUEST_TIMEOUT = 10            # Timeout HTTP (en secondes) appliqué à tous les appels de ce DAG.
HEALTH_CHECK_LATITUDE = 48.85   # Pour le health check
HEALTH_CHECK_LONGITUDE = 2.35

# ---------------------------------------------------------------------------
# default_args : paramètres hérités par TOUTES les tasks du DAG
# ---------------------------------------------------------------------------
default_args = {
    "owner": "admin",
    "retries": 2,                         # nb de tentatives avant FAILED définitif
    "retry_delay": timedelta(minutes=5),  # délai entre 2 tentatives
}


@dag(
    dag_id="nappecast_fetch_external_apis",
    description="Récupère les données Hubeau + OpenWeather via l'API NappeCast",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nappecast", "ingestion"],
    doc_md=__doc__,
)

def nappecast_fetch_external_apis():
    @task
    def check_hubeau_health() -> None:
        """
        Teste directement l'API Hubeau
        """
        endpoint = f"{HUBEAU_BASE_URL}/stations"
        params = {"size": 1}
        logger.info("Health check Hubeau sur %s", endpoint)
 
        response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
 
        if response.status_code not in (200, 206):
            raise AirflowException(
                f"Hubeau KO (status {response.status_code}) sur {endpoint}"
            )

        payload = response.json()
        if "count" not in payload:
            raise AirflowException(
                f"Hubeau a répondu 200 mais avec un format inattendu : {payload}"
            )
 
        logger.info("Hubeau OK (status %s, count=%s)", response.status_code, payload["count"])

    @task
    def check_openweather_health() -> None:
        """
        Teste directement l'API Open-Meteo.
        """
                
        endpoint = f"{OPEN_METEO_BASE_URL}/archive"
        params = {
            "latitude": HEALTH_CHECK_LATITUDE,
            "longitude": HEALTH_CHECK_LONGITUDE,
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "hourly": "temperature_2m",
        }
        logger.info("Health check Open-Meteo sur %s", endpoint)
 
        response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
 
        if response.status_code != 200:
            raise AirflowException(
                f"Open-Meteo KO (status {response.status_code}) : {response.text}"
            )
 
        payload = response.json()
        if "hourly" not in payload:
            raise AirflowException(
                f"Open-Meteo a répondu 200 mais avec un format inattendu : {payload}"
            )
 
        logger.info("Open-Meteo OK (status %s)", response.status_code)
        
    @task
    def fetch_data() -> dict:
        """
        Déclenche la récupération des données via la'API NappeCsat
        """
        endpoint = f"{API_BASE_URL}/pipeline/collect" 
        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() 

        result = response.json()
        logger.info("Récupération Hibeau OK : %s", result)
        return result


    health_checks_passed = EmptyOperator(task_id="health_checks_passed")
    hubeau_health = check_hubeau_health()
    openweather_health = check_openweather_health()
    collect_data = fetch_data()

    [hubeau_health, openweather_health] >> health_checks_passed
    health_checks_passed >> collect_data

nappecast_fetch_external_apis()