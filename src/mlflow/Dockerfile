FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow boto3
RUN pip install psycopg2-binary

EXPOSE 5000

CMD mlflow server \
    --backend-store-uri postgresql://postgres:LHopd10aald@mlflow.cp4kw66ewhrk.eu-west-3.rds.amazonaws.com:5432/postgres \
    --default-artifact-root s3://nappecast/mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    --workers 1 \
    --allowed-hosts "*" \
    --cors-allowed-origins "http://52.47.156.224:5000"