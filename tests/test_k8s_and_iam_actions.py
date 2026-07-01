import os

os.environ.setdefault("K8S_MODE", "simulated")

from services.remediation_agent import k8s_actions  # noqa: E402
from services.remediation_agent.iam_client import revoke_credential  # noqa: E402


def test_isolate_pod_simulated_mode_succeeds_without_cluster():
    result = k8s_actions.isolate_pod("demo-workloads", "payments-api-abc123")
    assert result.success is True
    assert result.mode == "simulated"
    assert "payments-api-abc123" in result.details


def test_release_pod_simulated_mode_succeeds_without_cluster():
    result = k8s_actions.release_pod("demo-workloads", "payments-api-abc123")
    assert result.success is True
    assert result.mode == "simulated"


def test_revoke_credential_reports_failure_when_iam_unreachable():
    # No mock-iam-service running in the unit test environment - this
    # should fail gracefully (not raise) and say why.
    result = revoke_credential("nonexistent-host-user", reason="unit test")
    assert result.success is False
    assert "mock IAM call failed" in result.details
