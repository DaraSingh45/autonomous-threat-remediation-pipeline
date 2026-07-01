import os
import sys
import time
import uuid
from concurrent import futures

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "proto", "generated", "python"))
import pipeline_pb2  # noqa: E402
import pipeline_pb2_grpc  # noqa: E402

from prometheus_client import Counter, Histogram  # noqa: E402

from services.common.kafka_utils import build_producer, publish, wait_for_kafka  # noqa: E402
from services.common.logging_config import get_logger, log_fields  # noqa: E402
from services.common.metrics import start_metrics_server  # noqa: E402
from services.common.schemas import AuditRecord  # noqa: E402
from services.decision_engine.policy import AUTONOMOUS_MODE, DedupCache, decide  # noqa: E402

logger = get_logger("decision_engine")

GRPC_PORT = os.environ.get("GRPC_PORT", "50051")
REMEDIATION_AGENT_ADDR = os.environ.get("REMEDIATION_AGENT_ADDR", "remediation-agent:50052")
AUDIT_TOPIC = os.environ.get("AUDIT_TOPIC", "audit-log")

DECISIONS = Counter("decisions_total", "Decisions made by the Decision Engine", ["action", "approved", "mode"])
DECISION_LATENCY = Histogram(
    "decision_latency_ms",
    "Time spent evaluating policy and (if approved) waiting on remediation",
    ["mode"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 5000, 15000, 30000),
)
REMEDIATION_CALL_ERRORS = Counter("remediation_agent_call_errors_total", "Failed gRPC calls to the Remediation Agent")


class DecisionServicer(pipeline_pb2_grpc.DecisionServiceServicer):
    def __init__(self):
        self.dedup = DedupCache()
        self.audit_producer = build_producer()
        channel = grpc.insecure_channel(REMEDIATION_AGENT_ADDR)
        self.remediation_stub = pipeline_pb2_grpc.RemediationServiceStub(channel)

    def HealthCheck(self, request, context):
        return pipeline_pb2.HealthCheckResponse(status="SERVING")

    def EvaluateThreat(self, request: pipeline_pb2.ThreatDetection, context):
        start = time.time()
        decision_id = str(uuid.uuid4())
        entity_key = f"{request.entity_type}:{request.entity_id}"
        mode_label = "autonomous" if AUTONOMOUS_MODE else "manual_simulated"

        decision = decide(request.entity_type, request.severity, self.dedup)

        remediation_id = ""
        remediation_success = False
        remediation_details = "no remediation attempted"
        remediation_started_ms = None
        completed_at_ms = None

        if decision.approved and self.dedup.should_suppress(entity_key):
            decision.approved = False
            decision.reasoning = f"suppressed: {entity_key} already remediated within cooldown window"

        if decision.approved:
            if decision.simulated_delay_s > 0:
                logger.info(
                    f"Simulating manual analyst triage delay of {decision.simulated_delay_s}s for {entity_key} "
                    f"(AUTONOMOUS_MODE=false — this models the MTTR baseline before automation)"
                )
                time.sleep(decision.simulated_delay_s)

            remediation_started_ms = int(time.time() * 1000)
            remediation_request = pipeline_pb2.RemediationRequest(
                decision_id=decision_id,
                event_id=request.event_id,
                detection_id=request.detection_id,
                action=decision.action,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                namespace=request.namespace,
                severity=request.severity,
                reasoning=decision.reasoning,
            )
            try:
                remediation_response = self.remediation_stub.ExecuteRemediation(remediation_request, timeout=10)
                remediation_id = remediation_response.remediation_id
                remediation_success = remediation_response.success
                remediation_details = remediation_response.details
                completed_at_ms = remediation_response.completed_at_ms
                self.dedup.mark_actioned(entity_key)
            except grpc.RpcError as exc:
                REMEDIATION_CALL_ERRORS.inc()
                remediation_details = f"remediation call failed: {exc.code()} {exc.details()}"
                completed_at_ms = int(time.time() * 1000)
                logger.error(remediation_details, extra=log_fields(entity_key=entity_key, decision_id=decision_id))

        decided_at_ms = int(time.time() * 1000)
        elapsed_ms = (time.time() - start) * 1000
        DECISION_LATENCY.labels(mode=mode_label).observe(elapsed_ms)
        DECISIONS.labels(action=decision.action, approved=str(decision.approved), mode=mode_label).inc()

        self._publish_audit_record(
            request, decision, decision_id, mode_label, remediation_id,
            remediation_started_ms, completed_at_ms, remediation_success, remediation_details,
        )

        logger.info(
            f"Decision: action={decision.action} approved={decision.approved} mode={mode_label}",
            extra=log_fields(
                decision_id=decision_id, entity_key=entity_key, action=decision.action,
                approved=decision.approved, remediation_success=remediation_success,
            ),
        )

        return pipeline_pb2.DecisionResponse(
            decision_id=decision_id,
            approved=decision.approved,
            action=decision.action,
            reasoning=decision.reasoning,
            autonomous=AUTONOMOUS_MODE,
            decided_at_ms=decided_at_ms,
            remediation_success=remediation_success,
            remediation_details=remediation_details,
            remediation_id=remediation_id,
        )

    def _publish_audit_record(
        self, request, decision, decision_id, mode_label, remediation_id,
        remediation_started_ms, completed_at_ms, remediation_success, remediation_details,
    ):
        mttd_ms = max(request.detected_at_ms - request.event_timestamp_ms, 0)
        mttr_ms = None
        if completed_at_ms is not None:
            mttr_ms = max(completed_at_ms - request.detected_at_ms, 0)

        record = AuditRecord(
            event_id=request.event_id,
            detection_id=request.detection_id,
            decision_id=decision_id,
            remediation_id=remediation_id or None,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            namespace=request.namespace or None,
            severity=request.severity,
            event_type=request.event_type,
            action=decision.action,
            mode=mode_label,
            detection_source=request.detection_source,
            rule_name=request.rule_name or None,
            anomaly_score=request.anomaly_score,
            event_timestamp_ms=request.event_timestamp_ms,
            detected_at_ms=request.detected_at_ms,
            decided_at_ms=int(time.time() * 1000),
            remediation_started_ms=remediation_started_ms,
            completed_at_ms=completed_at_ms,
            mttd_ms=mttd_ms,
            mttr_ms=mttr_ms,
            success=remediation_success if decision.approved else True,
            details=remediation_details,
            raw_event=_safe_json(request.raw_event_json),
        )
        publish(self.audit_producer, AUDIT_TOPIC, record.model_dump(mode="json"), key=request.entity_id)


def _safe_json(raw: str) -> dict:
    import json

    try:
        return json.loads(raw)
    except Exception:
        return {}


def serve():
    start_metrics_server(default_port=9102)
    wait_for_kafka()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    pipeline_pb2_grpc.add_DecisionServiceServicer_to_server(DecisionServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    logger.info(
        f"Decision Engine gRPC server listening on :{GRPC_PORT} "
        f"(AUTONOMOUS_MODE={AUTONOMOUS_MODE}, remediation_agent={REMEDIATION_AGENT_ADDR})"
    )
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
