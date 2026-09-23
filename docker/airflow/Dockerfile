FROM apache/airflow:3.1.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

# Contexte de build = racine du dépôt (voir le workflow)
COPY docker/airflow/requirements.txt .
# On réinstalle la version d'Airflow de l'image pour que pip ne la change pas
RUN pip install --no-cache-dir "apache-airflow==3.1.3" -r requirements.txt

ENV PYTHONPATH=/opt/airflow
