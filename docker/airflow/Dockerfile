FROM apache/airflow:3.1.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt .

RUN pip install --no-cache-dir \
      "apache-airflow==${AIRFLOW_VERSION}" \
      -r requirements.txt \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_MAJOR_MINOR_VERSION}.txt"

ENV PYTHONPATH=/opt/airflow