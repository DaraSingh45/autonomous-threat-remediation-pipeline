
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

from services.common.logging_config import get_logger, log_fields  # noqa: E402
from services.common.metrics import start_metrics_server  # noqa: E402
from services.remediation_agent.iam_client import revoke_credential  # noqa: E402
from services.remediation_agent.k8s_actions import K8S_MODE, isolate_pod  # noqa: E402

logger = get_logger("remediation_agent")

GRPC_PORT = os.environ.get("GRPC_PORT", "50052")

REMEDIATION_ACTIONS = Counter(
    "remediation_actions_total", "Remediation actions executed", ["action", "status", "mode"]
)
REMEDIATION_LATENCY = Histogram(
    "remediation_latency_ms",
    "Time to execute a remediation action once dispatched",
    ["action"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500),
)


class RemediationServicer(pipeline_pb2_grpc.RemediationServiceServicer):
    def HealthCheck(self, request, context):
        return pipeline_pb2.HealthCheckResponse(status="SERVING")

    def ExecuteRemediation(self, request: pipeline_pb2.RemediationRequest, context):
        start = time.time()
        remediation_id = str(uuid.uuid4())
        started_ms = int(time.time() * 1000)

        logger.info(
            f"Executing remediation: action={request.action} entity={request.entity_type}:{request.entity_id}",
            extra=log_fields(decision_id=request.decision_id, action=request.action, entity_id=request.entity_id),
        )

        if request.action == "isolate_pod":
            result = isolate_pod(request.namespace or "demo-workloads", request.entity_id)
            mode = result.mode
            success, details = result.success, result.details
        elif request.action == "revoke_credential":
            result = revoke_credential(request.entity_id, request.reasoning)
            mode = "real"  # mock IAM is always "really" called, it's just a mock backend
            success, details = result.success, result.details
        else:
            mode = "n/a"
            success, details = False, f"unknown action type '{request.action}'"

        completed_at_ms = int(time.time() * 1000)
        elapsed_ms = (time.time() - start) * 1000

        REMEDIATION_ACTIONS.labels(action=request.action, status="success" if success else "failed", mode=mode).inc()
        REMEDIATION_LATENCY.labels(action=request.action).observe(elapsed_ms)

        logger.info(
            f"Remediation {'succeeded' if success else 'failed'}: {details}",
            extra=log_fields(remediation_id=remediation_id, success=success, mode=mode, elapsed_ms=elapsed_ms),
        )

        return pipeline_pb2.RemediationResponse(
            remediation_id=remediation_id,
            success=success,
            details=details,
            remediation_started_ms=started_ms,
            completed_at_ms=completed_at_ms,
            mode=mode,
        )


def serve():
    start_metrics_server(default_port=9103)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    pipeline_pb2_grpc.add_RemediationServiceServicer_to_server(RemediationServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    logger.info(f"Remediation Agent gRPC server listening on :{GRPC_PORT} (K8S_MODE={K8S_MODE})")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
