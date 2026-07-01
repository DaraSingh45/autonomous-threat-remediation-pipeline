FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=decision-engine \
    PYTHONPATH=/app

WORKDIR /app

COPY services/decision_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/__init__.py ./services/__init__.py
COPY services/decision_engine ./services/decision_engine
COPY proto/generated/python ./proto/generated/python

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 50051 9102

CMD ["python", "-m", "services.decision_engine.server"]
