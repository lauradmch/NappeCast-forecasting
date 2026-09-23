"""
DAG : nappecast_daily_predict
====================================

BUT DU DAG
----------
Déclencher, via l'API NappeCast (172.31.41.22:8000), la récupération des
données provenant des APIs externes Hibeau et OpenWeather et lancer le predict

Déroulé :
    1a. check_hubeau_health         -> teste directement l'API Hubeau.(1a et 1b tournent en parrallèle)
    1b. check_openweather_health    -> teste directement l'API OpenWeather. (1a et 1b tournent en parrallèle)
    2.  health_checks_passed        -> tâche de JONCTION (vide pour l'instant), qui attend que 1a ET 1b.
    3.  fetch_data                  -> déclenche la récupération des datas.
    4a.  predict_h14                -> Prediction sur un forecast de 14 jours (4a et 4b tournent en parrallèle)
    4b.  predict_h30                -> Prediction sur un forecast de 30 jours (4a et 4b tournent en parrallèle)
    
    5. extract_csv_from_s3          -> télécharge le CSV processed depuis S3 vers un fichier temporaire local
    6. create_table_if_needed       -> lit l'en-tête du CSV et crée la table cible dans RDS si elle n'existe pas encore 
    7. load_csv_to_rds              -> charge le CSV dans la table
    8. cleanup_tmp_file             -> supprime le fichier temporaire local
"""
import logging
from xml.parsers.expat import model
import requests

from typing import  Literal
from pathlib import Path
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from src.api.main import forecast
from __future__ import annotations

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

REQUEST_TIMEOUT         = 120            # Timeout HTTP (en secondes) appliqué à tous les appels de ce DAG.
HEALTH_CHECK_LATITUDE   = 48.85   # Pour le health check
HEALTH_CHECK_LONGITUDE  = 2.35
PIPELINE_SECRET         = Variable.get("pipeline_secret")

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
    description="Récupère les données Hubeau + OpenWeather via l'API NappeCast + prédiction + archivage en db",
    default_args=default_args,
    schedule="0 6 * * *", # tous les jours à 6h
    start_date=datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    tags=["pipeline data", "rds", "postgres", "s3", "csv"],
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
                f"Hubeau KO (status {response.status_code}) sur {endpoint}:{response.text}"
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
                f"Open-Meteo KO (status {response.status_code}) sur {endpoint}:{response.text}"
            )
 
        payload = response.json()
        if "hourly" not in payload:
            raise AirflowException(
                f"Open-Meteo a répondu 200 mais avec un format inattendu : {payload}"
            )
 
        logger.info("Open-Meteo OK (status %s)", response.status_code)
        
    @task
    def collect() -> dict:
        """
        Déclenche la récupération des données via la'API NappeCsat
        """
        endpoint = f"{API_BASE_URL}/pipeline/collect"
        headers = {"X-Pipeline-Secret": PIPELINE_SECRET}

        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, timeout=REQUEST_TIMEOUT, headers=headers)

        if response.status_code >= 400:
            logger.error("Réponse API pipeline/collect (%s) : %s", response.status_code, response.text)

        response.raise_for_status()
        result = response.json()

        logger.info("Récupération Hibeau OK : %s", result)
        return result

    @task
    def transform() -> dict:
        """
        Déclenche le feature ingineering sur les données interim
        """
        endpoint = f"{API_BASE_URL}/pipeline/transform"
        headers = {"X-Pipeline-Secret": PIPELINE_SECRET}

        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, timeout=REQUEST_TIMEOUT, headers=headers)

        if response.status_code >= 400:
            logger.error("Réponse API pipeline/transform (%s) : %s", response.status_code, response.text)

        response.raise_for_status()
        result = response.json()

        logger.info("Transform OK : %s", result)
        return result

    @task
    def predict(horizon: Literal[14, 30],) -> dict:
        """
        Déclenche le predict pour un forecast
        """
        endpoint = f"{API_BASE_URL}/pipeline/forecast"
        headers = {"X-Pipeline-Secret": PIPELINE_SECRET}

        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, timeout=REQUEST_TIMEOUT, params={"H": horizon}, headers=headers)

        if response.status_code >= 400:
            logger.error("Réponse API pipeline/transform (%s) : %s", response.status_code, response.text)

        response.raise_for_status()
        result = response.json()

        logger.info("Predict H%s OK : %s", horizon, result)
        return result       


    @task
    def load() -> None:
        """
        Charge les datas dans RDS
        """

        endpoint = f"{API_BASE_URL}/pipeline/load"
        headers = {"X-Pipeline-Secret": PIPELINE_SECRET}

        logger.info("Appel de %s", endpoint)

        response = requests.post(endpoint, timeout=REQUEST_TIMEOUT, headers=headers)

        if response.status_code >= 400:
            logger.error("Réponse API pipeline/load (%s) : %s", response.status_code, response.text)

        response.raise_for_status()
        result = response.json()

        logger.info("Load OK : %s", result)
        return result       

    health_checks_passed = EmptyOperator(task_id="health_checks_passed")
    hubeau_health = check_hubeau_health()
    openweather_health = check_openweather_health()
    collect_data = collect()
    transform_data = transform()
    predictH14 = predict(horizon=14)
    predictH30 = predict(horizon=30)
    load_data = load()
    
    [hubeau_health, openweather_health] >> health_checks_passed
    health_checks_passed >> collect_data
    collect_data >> transform
    transform_data >> [predictH14,predictH30]
    [predictH14,predictH30] >> load_data

nappecast_fetch_external_apis()