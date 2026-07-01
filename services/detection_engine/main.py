import os
import signal
import sys
import time
import uuid

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "proto", "generated", "python"))
import pipeline_pb2  # noqa: E402
import pipeline_pb2_grpc  # noqa: E402

from prometheus_client import Counter, Histogram  # noqa: E402

from services.common.kafka_utils import build_consumer, wait_for_kafka  # noqa: E402
from services.common.logging_config import get_logger, log_fields  # noqa: E402
from services.common.metrics import start_metrics_server  # noqa: E402
from services.common.schemas import SecurityEvent, Severity  # noqa: E402
from services.detection_engine.anomaly_model import AnomalyDetector  # noqa: E402
from services.detection_engine.rule_engine import evaluate_rules  # noqa: E402

logger = get_logger("detection_engine")

EVENTS_TOPIC = os.environ.get("EVENTS_TOPIC", "security-events")
DECISION_ENGINE_ADDR = os.environ.get("DECISION_ENGINE_ADDR", "decision-engine:50051")
SEVERITY_RANK = {Severity.INFO: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
MIN_SEVERITY_TO_ESCALATE = Severity(os.environ.get("MIN_SEVERITY_TO_ESCALATE", "medium"))

EVENTS_CONSUMED = Counter("events_consumed_total", "Raw security events consumed from Kafka")
THREATS_DETECTED = Counter(
    "threats_detected_total", "Detections escalated to the Decision Engine", ["severity", "source"]
)
DETECTION_LATENCY = Histogram(
    "detection_latency_ms",
    "Time from event timestamp to detection completion (contributes to MTTD)",
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)
DECISION_CALL_ERRORS = Counter("decision_engine_call_errors_total", "Failed gRPC calls to the Decision Engine")

# Which entity the remediation should target, derived from the event.
POD_EVENT_TYPES = {"process_spawn", "network_egress", "privilege_escalation"}
USER_EVENT_TYPES = {"failed_login"}

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down gracefully")
    _shutdown = True


def _entity_for(event: SecurityEvent):
    if event.event_type.value in POD_EVENT_TYPES and event.pod_name:
        return "pod", event.pod_name
    if event.event_type.value in USER_EVENT_TYPES and event.user:
        return "user", event.user
    # port scans etc. - target the source host as a fallback
    return "host", event.source_ip


def build_grpc_stub():
    channel = grpc.insecure_channel(DECISION_ENGINE_ADDR)
    return pipeline_pb2_grpc.DecisionServiceStub(channel)


def process_event(raw: dict, stub) -> None:
    EVENTS_CONSUMED.inc()
    event = SecurityEvent.model_validate(raw)

    rule_match = evaluate_rules(event)
    detector = process_event.detector  # attached once at module load, see main()
    anomaly = detector.score(event)

    severity = None
    source = None
    rule_name = None
    anomaly_score = anomaly.score

    if rule_match and anomaly.is_anomalous:
        source = "hybrid"
        rule_name = rule_match.rule_name
        severity = rule_match.severity if SEVERITY_RANK[rule_match.severity] >= SEVERITY_RANK[anomaly.severity] else anomaly.severity
    elif rule_match:
        source = "rule_engine"
        rule_name = rule_match.rule_name
        severity = rule_match.severity
    elif anomaly.is_anomalous:
        source = "isolation_forest"
        severity = anomaly.severity

    detected_at_ms = int(time.time() * 1000)
    latency_ms = detected_at_ms - event.timestamp_ms
    if severity is not None:
        DETECTION_LATENCY.observe(max(latency_ms, 0))

    if severity is None or SEVERITY_RANK[severity] < SEVERITY_RANK[MIN_SEVERITY_TO_ESCALATE]:
        return  # benign / below escalation threshold - nothing further to do

    THREATS_DETECTED.labels(severity=severity.value, source=source).inc()
    entity_type, entity_id = _entity_for(event)

    detection = pipeline_pb2.ThreatDetection(
        event_id=event.event_id,
        detection_id=str(uuid.uuid4()),
        event_timestamp_ms=event.timestamp_ms,
        detected_at_ms=detected_at_ms,
        detection_source=source,
        rule_name=rule_name or "",
        anomaly_score=anomaly_score,
        severity=severity.value,
        entity_type=entity_type,
        entity_id=entity_id,
        namespace=event.namespace or "",
        event_type=event.event_type.value,
        raw_event_json=event.model_dump_json(),
    )

    logger.info(
        f"Threat detected: {severity.value} via {source} on {entity_type}={entity_id}",
        extra=log_fields(
            event_id=event.event_id, severity=severity.value, source=source, rule_name=rule_name,
            entity_type=entity_type, entity_id=entity_id, detection_latency_ms=latency_ms,
        ),
    )

    try:
        response = stub.EvaluateThreat(detection, timeout=5)
        logger.info(
            f"Decision Engine responded: approved={response.approved} action={response.action}",
            extra=log_fields(decision_id=response.decision_id, approved=response.approved, action=response.action),
        )
    except grpc.RpcError as exc:
        DECISION_CALL_ERRORS.inc()
        logger.error(f"gRPC call to Decision Engine failed: {exc.code()} {exc.details()}")


def main():
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    start_metrics_server(default_port=9101)
    wait_for_kafka()

    process_event.detector = AnomalyDetector()
    logger.info("Isolation Forest anomaly model loaded")

    stub = build_grpc_stub()
    consumer = build_consumer(topics=[EVENTS_TOPIC], group_id="detection-engine")
    logger.info(f"Detection Engine consuming from '{EVENTS_TOPIC}', calling Decision Engine at {DECISION_ENGINE_ADDR}")

    while not _shutdown:
        for message in consumer:
            try:
                process_event(message.value, stub)
            except Exception:
                logger.exception("Error processing event; continuing")
            if _shutdown:
                break

    consumer.close()
    logger.info("Detection Engine stopped cleanly")


if __name__ == "__main__":
    main()
