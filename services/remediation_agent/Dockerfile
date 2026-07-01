FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=remediation-agent \
    PYTHONPATH=/app

WORKDIR /app

COPY services/remediation_agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/__init__.py ./services/__init__.py
COPY services/remediation_agent ./services/remediation_agent
COPY proto/generated/python ./proto/generated/python

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 50052 9103

CMD ["python", "-m", "services.remediation_agent.server"]
