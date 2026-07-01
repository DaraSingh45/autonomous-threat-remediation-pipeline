import os
from prometheus_client import start_http_server

from services.common.logging_config import get_logger

logger = get_logger(__name__)


def start_metrics_server(default_port: int) -> None:
    port = int(os.environ.get("METRICS_PORT", default_port))
    start_http_server(port)
    logger.info(f"Prometheus metrics server listening on :{port}/metrics")
