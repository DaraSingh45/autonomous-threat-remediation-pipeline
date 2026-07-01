FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=event-generator \
    PYTHONPATH=/app

WORKDIR /app

COPY services/event_generator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/__init__.py ./services/__init__.py
COPY services/event_generator ./services/event_generator

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 9100

CMD ["python", "-m", "services.event_generator.generator"]
