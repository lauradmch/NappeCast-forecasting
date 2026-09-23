FROM apache/airflow:3.1.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt .

RUN PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")') && \
    pip install --no-cache-dir \
      "apache-airflow==${AIRFLOW_VERSION}" \
      -r requirements.txt \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

ENV PYTHONPATH=/opt/airflow