#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/airflow
SECRET_ID="airflow/prod-latest"
REGION="eu-west-3"
ECR_REGISTRY="844099234486.dkr.ecr.eu-west-3.amazonaws.com"

cd "$APP_DIR"
for f in docker-compose.yml airflow.env; do
  [ -f "$f" ] || { echo "ERREUR : $APP_DIR/$f manquant"; exit 1; }
done

# 1. Secrets -> .env.runtime (lisible par root uniquement)
umask 077
aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --region "$REGION" \
  --query SecretString --output text > .secret.json
if ! jq -e 'type == "object"' .secret.json >/dev/null 2>&1; then
  rm -f .secret.json
  echo "ERREUR : le secret $SECRET_ID n'est pas un JSON valide"
  exit 1
fi
jq -r 'to_entries[] | "\(.key)=\(.value)"' .secret.json > .env.runtime
rm -f .secret.json
umask 022

# 2. Dossiers montés dans les conteneurs (utilisateur airflow = 50000)
mkdir -p dags logs plugins config data
chown 50000:0 dags logs plugins config data

# 3. Image + démarrage
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker compose --env-file airflow.env pull
docker compose --env-file airflow.env up -d --remove-orphans
docker image prune -f
docker compose --env-file airflow.env ps
