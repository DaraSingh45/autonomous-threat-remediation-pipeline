import os
import signal
import time

from prometheus_client import Counter

from services.common.kafka_utils import build_producer, publish, wait_for_kafka
from services.common.logging_config import get_logger
from services.common.metrics import start_metrics_server
from services.event_generator.scenarios import generate_stream

logger = get_logger("event_generator")

EVENTS_TOPIC = os.environ.get("EVENTS_TOPIC", "security-events")
EVENTS_PER_SECOND = float(os.environ.get("EVENTS_PER_SECOND", "5"))
ATTACK_PROBABILITY = float(os.environ.get("ATTACK_PROBABILITY", "0.08"))

EVENTS_PRODUCED = Counter(
    "events_produced_total", "Synthetic security events published to Kafka", ["event_type", "scenario_tag"]
)

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down gracefully")
    _shutdown = True


def main():
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    start_metrics_server(default_port=9100)
    wait_for_kafka()
    producer = build_producer()

    sleep_interval = 1.0 / max(EVENTS_PER_SECOND, 0.1)
    logger.info(
        f"Event generator starting: ~{EVENTS_PER_SECOND} events/sec, "
        f"attack_probability={ATTACK_PROBABILITY}, topic={EVENTS_TOPIC}"
    )

    produced = 0
    while not _shutdown:
        for event in generate_stream(ATTACK_PROBABILITY):
            payload = event.model_dump(mode="json")
            key = event.pod_name or event.user or event.source_ip
            publish(producer, EVENTS_TOPIC, payload, key=key)
            EVENTS_PRODUCED.labels(event_type=event.event_type.value, scenario_tag=event.scenario_tag.value).inc()
            produced += 1
            if produced % 50 == 0:
                logger.info(f"Produced {produced} events so far")
        time.sleep(sleep_interval)

    producer.flush(timeout=5)
    producer.close(timeout=5)
    logger.info("Event generator stopped cleanly")


if __name__ == "__main__":
    main()
