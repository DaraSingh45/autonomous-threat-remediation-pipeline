FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=detection-engine \
    PYTHONPATH=/app

WORKDIR /app

COPY services/detection_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/__init__.py ./services/__init__.py
COPY services/detection_engine ./services/detection_engine
COPY proto/generated/python ./proto/generated/python

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 9101

CMD ["python", "-m", "services.detection_engine.main"]
