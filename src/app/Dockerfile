FROM python:3.11-slim

WORKDIR /home/app

# Dépendances installées en premier pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY . .

ENV PORT=8501
EXPOSE $PORT

CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true