FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=mock-iam-service \
    PYTHONPATH=/app

WORKDIR /app

COPY services/mock_iam_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/__init__.py ./services/__init__.py
COPY services/mock_iam_service ./services/mock_iam_service

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "services.mock_iam_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
