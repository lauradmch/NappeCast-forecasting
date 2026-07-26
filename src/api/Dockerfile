FROM python:3.11-slim

WORKDIR /home/app

COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY configs/ ./configs/

ENV PORT=8000
EXPOSE $PORT

CMD uvicorn src.api.main:app --host 0.0.0.0 --port $PORT