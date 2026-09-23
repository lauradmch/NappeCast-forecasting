FROM apache/airflow:2.11.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt .

RUN pip install --no-cache-dir "apache-airflow==3.1.3" -r requirements.txt

ENV PYTHONPATH=/opt/airflow