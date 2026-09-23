FROM python:3.11-slim

# Même version que le client MLflow utilisé par Airflow
RUN pip install --no-cache-dir "mlflow==3.14.0" boto3 psycopg2-binary

EXPOSE 5000

CMD mlflow server \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
    --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" \
    --host 0.0.0.0 \
    --port 5000 \
    --workers 1 \
    --allowed-hosts "*" \
    --cors-allowed-origins "$CORS_ALLOWED_ORIGINS"
