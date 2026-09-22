FROM apache/airflow:3.1.3

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

COPY docker/airflow/requirements.txt . 

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /opt/airflow/src/
COPY configs/ /opt/airflow/configs/


ENV PYTHONPATH=/opt/airflow