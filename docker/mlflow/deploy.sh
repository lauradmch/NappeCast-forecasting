#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/mlflow
ENV_FILE="$APP_DIR/.env.runtime"
SECRET_ID="mlflow/prod3"
REGION="eu-west-3"
ECR_REGISTRY="844099234486.dkr.ecr.eu-west-3.amazonaws.com"

# 1. Récupérer les secrets
umask 077
aws secretsmanager get-secret-value \
--secret-id "$SECRET_ID" \
--region "$REGION" \
--query SecretString --output text \
| jq -r 'to_entries[] | "\(.key)=\(.value)"' > "$ENV_FILE"

chmod 600 "$ENV_FILE"
chown appuser:appuser "$ENV_FILE" "$APP_DIR/docker-compose.yml"

# 2. Authentification au registre puis démarrage
aws ecr get-login-password --region "$REGION" \
| docker login --username AWS --password-stdin "$ECR_REGISTRY"

cd "$APP_DIR"
docker compose pull
docker compose --env-file "$ENV_FILE" up -d
docker image prune -f