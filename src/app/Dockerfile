FROM python:3.11-slim

WORKDIR /home/app

# Dépendances installées en premier pour profiter du cache Docker
COPY src/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY src/ ./src/
COPY configs/ ./configs/

ENV PORT=8501
# pour eviter le pb d'interpretation de chemin
# Streamlit ajoute le dossier du script (/home/app/src/app) à sys.path
ENV PYTHONPATH=/home/app   


EXPOSE $PORT

CMD streamlit run src/app/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true