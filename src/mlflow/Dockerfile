FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow boto3

EXPOSE 5000

CMD mlflow server \
    --backend-store-uri sqlite:////mlflow-data/mlflow.db \
    --default-artifact-root s3://nappecast/mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    --workers 1 \
    --allowed-hosts "*"