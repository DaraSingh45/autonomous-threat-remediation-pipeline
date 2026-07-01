from __future__ import annotations

import json
import os
import time
from typing import Iterable, Optional

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

from services.common.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def wait_for_kafka(bootstrap_servers: str = DEFAULT_BOOTSTRAP, timeout_s: int = 60) -> None:
    """Block until Kafka accepts connections, or raise after `timeout_s`.

    docker-compose starts containers in parallel, so consumers/producers
    routinely start before the broker has finished forming its cluster
    metadata. Rather than relying on `depends_on: condition: service_healthy`
    alone, each service retries its own connection - this makes the system
    resilient to slow starts in CI and on constrained laptops too.
    """
    deadline = time.time() + timeout_s
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            producer = KafkaProducer(bootstrap_servers=bootstrap_servers, request_timeout_ms=3000)
            producer.close(timeout=1)
            logger.info(f"Kafka is reachable at {bootstrap_servers}")
            return
        except NoBrokersAvailable as exc:
            last_err = exc
            time.sleep(2)
    raise RuntimeError(f"Kafka not reachable at {bootstrap_servers} after {timeout_s}s") from last_err


def build_producer(bootstrap_servers: str = DEFAULT_BOOTSTRAP) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",
        retries=5,
        linger_ms=20,  # small batching window - real "high throughput backplane" behavior
    )


def build_consumer(
    topics: Iterable[str],
    group_id: str,
    bootstrap_servers: str = DEFAULT_BOOTSTRAP,
    auto_offset_reset: str = "earliest",
) -> KafkaConsumer:
    return KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=True,
        auto_commit_interval_ms=1000,
        consumer_timeout_ms=1000,  # yields control periodically so services can check shutdown flags
    )


def publish(producer: KafkaProducer, topic: str, value: dict, key: Optional[str] = None) -> None:
    producer.send(topic, key=key, value=value)
