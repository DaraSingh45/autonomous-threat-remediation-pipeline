

from __future__ import annotations

import os
from dataclasses import dataclass

from services.common.logging_config import get_logger

logger = get_logger("remediation_agent.k8s_actions")

K8S_MODE = os.environ.get("K8S_MODE", "simulated").lower()


@dataclass
class K8sActionResult:
    success: bool
    details: str
    mode: str


def _load_k8s_client():
    from kubernetes import client, config

    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config")
    except Exception:
        config.load_kube_config()
        logger.info("Loaded local kubeconfig for Kubernetes access")
    return client


def isolate_pod(namespace: str, pod_name: str) -> K8sActionResult:
    if K8S_MODE != "real":
        logger.info(f"[SIMULATED] Would label pod {namespace}/{pod_name} quarantine=true and apply deny-all NetworkPolicy")
        return K8sActionResult(
            success=True,
            details=f"[SIMULATED] labeled {namespace}/{pod_name} quarantine=true; applied deny-all NetworkPolicy "
                     f"'quarantine-{pod_name}' (no live cluster connected - set K8S_MODE=real to perform this for real)",
            mode="simulated",
        )

    client = _load_k8s_client()
    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    # 1. Label the pod for quarantine / observability.
    core_v1.patch_namespaced_pod(
        name=pod_name,
        namespace=namespace,
        body={"metadata": {"labels": {"quarantine": "true"}}},
    )

    # 2. Apply a deny-all ingress+egress NetworkPolicy targeting that label.
    policy_name = f"quarantine-{pod_name}"[:253]
    body = client.V1NetworkPolicy(
        metadata=client.V1ObjectMeta(name=policy_name, namespace=namespace),
        spec=client.V1NetworkPolicySpec(
            pod_selector=client.V1LabelSelector(match_labels={"quarantine": "true"}),
            policy_types=["Ingress", "Egress"],
            ingress=[],
            egress=[],
        ),
    )
    try:
        networking_v1.create_namespaced_network_policy(namespace=namespace, body=body)
    except client.exceptions.ApiException as exc:
        if exc.status == 409:  # already exists - fine, treat as idempotent success
            logger.info(f"NetworkPolicy {policy_name} already exists, treating isolate as already-applied")
        else:
            raise

    logger.info(f"Isolated pod {namespace}/{pod_name}: labeled + deny-all NetworkPolicy applied")
    return K8sActionResult(
        success=True,
        details=f"labeled {namespace}/{pod_name} quarantine=true; applied deny-all NetworkPolicy '{policy_name}'",
        mode="real",
    )


def release_pod(namespace: str, pod_name: str) -> K8sActionResult:
    """Rollback helper for demos/tests: remove the quarantine label and NetworkPolicy."""
    if K8S_MODE != "real":
        return K8sActionResult(success=True, details=f"[SIMULATED] released {namespace}/{pod_name}", mode="simulated")

    client = _load_k8s_client()
    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    core_v1.patch_namespaced_pod(
        name=pod_name, namespace=namespace, body={"metadata": {"labels": {"quarantine": None}}}
    )
    policy_name = f"quarantine-{pod_name}"[:253]
    try:
        networking_v1.delete_namespaced_network_policy(name=policy_name, namespace=namespace)
    except client.exceptions.ApiException as exc:
        if exc.status != 404:
            raise

    return K8sActionResult(success=True, details=f"released {namespace}/{pod_name}", mode="real")
