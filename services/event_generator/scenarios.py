"""
Synthetic telemetry scenarios.

`benign_event()` produces normal background noise. The `SCENARIOS` below
each produce a short burst of events that *look like* a specific attack
technique, so the rest of the pipeline (rule engine + Isolation Forest +
remediation) has something realistic to react to. These are not real attack
tools - they only synthesize the numeric/categorical telemetry fields an
EDR/CSPM agent would typically emit for that behavior.
"""

from __future__ import annotations

import random
from typing import Iterator

from services.common.schemas import EventType, ScenarioTag, SecurityEvent, Severity

NORMAL_USERS = ["alice", "bob", "carol", "dave", "svc-payments", "svc-billing", "erin"]
NORMAL_PROCESSES = ["python3", "nginx", "java", "node", "gunicorn", "sshd", "bash"]
SUSPICIOUS_PROCESSES = ["xmrig", "kinsing", "cryptominer.sh", "ncat", "masscan"]
KNOWN_BAD_IPS = ["185.220.101.7", "45.155.205.233", "194.165.16.71", "91.240.118.4"]
INTERNAL_IPS = [f"10.0.{i}.{j}" for i in range(1, 6) for j in (10, 20, 30, 40)]
DEMO_PODS = [
    "payments-api-7c9f4b8d6-x2z9k",
    "billing-worker-5f6d8c9b4-p8m2q",
    "checkout-frontend-6b7c8d9e5-n3v7r",
    "auth-service-8d9e6f7a2-k4t1w",
    "inventory-sync-4a5b6c7d8-q9r2s",
]


def _rand_ip(pool):
    return random.choice(pool)


def benign_event() -> SecurityEvent:
    event_type = random.choices(
        [EventType.FAILED_LOGIN, EventType.PROCESS_SPAWN, EventType.NETWORK_EGRESS, EventType.PORT_SCAN],
        weights=[0.15, 0.55, 0.25, 0.05],
    )[0]

    return SecurityEvent(
        event_type=event_type,
        severity_hint=Severity.INFO,
        source_ip=_rand_ip(INTERNAL_IPS),
        dest_ip=_rand_ip(INTERNAL_IPS),
        user=random.choice(NORMAL_USERS),
        namespace="demo-workloads",
        pod_name=random.choice(DEMO_PODS),
        process_name=random.choice(NORMAL_PROCESSES),
        bytes_transferred=random.randint(500, 50_000),
        login_attempts_last_5m=random.randint(0, 1),
        process_spawn_rate_last_1m=round(random.uniform(0.0, 1.5), 2),
        distinct_ports_last_1m=random.randint(1, 3),
        is_known_bad_ip=False,
        scenario_tag=ScenarioTag.BENIGN,
    )


def brute_force_scenario() -> Iterator[SecurityEvent]:
    """Rapid failed logins against a single account from one source IP."""
    target_user = random.choice(NORMAL_USERS)
    attacker_ip = _rand_ip(KNOWN_BAD_IPS + INTERNAL_IPS)
    burst = random.randint(6, 14)
    for i in range(burst):
        yield SecurityEvent(
            event_type=EventType.FAILED_LOGIN,
            severity_hint=Severity.MEDIUM,
            source_ip=attacker_ip,
            user=target_user,
            namespace="demo-workloads",
            login_attempts_last_5m=i + 1,
            is_known_bad_ip=attacker_ip in KNOWN_BAD_IPS,
            scenario_tag=ScenarioTag.BRUTE_FORCE,
            metadata={"technique": "T1110 - Brute Force"},
        )


def crypto_miner_scenario() -> Iterator[SecurityEvent]:
    """Unusual process spawn consistent with a cryptomining implant in a pod."""
    pod = random.choice(DEMO_PODS)
    proc = random.choice(SUSPICIOUS_PROCESSES)
    for _ in range(random.randint(2, 4)):
        yield SecurityEvent(
            event_type=EventType.PROCESS_SPAWN,
            severity_hint=Severity.HIGH,
            source_ip=_rand_ip(INTERNAL_IPS),
            dest_ip=_rand_ip(KNOWN_BAD_IPS),
            user="root",
            namespace="demo-workloads",
            pod_name=pod,
            process_name=proc,
            process_spawn_rate_last_1m=round(random.uniform(4.0, 9.0), 2),
            bytes_transferred=random.randint(1_000, 20_000),
            is_known_bad_ip=True,
            scenario_tag=ScenarioTag.CRYPTO_MINER,
            metadata={"technique": "T1496 - Resource Hijacking"},
        )


def data_exfiltration_scenario() -> Iterator[SecurityEvent]:
    """Large, anomalous egress transfer to an external destination."""
    pod = random.choice(DEMO_PODS)
    for _ in range(random.randint(1, 3)):
        yield SecurityEvent(
            event_type=EventType.NETWORK_EGRESS,
            severity_hint=Severity.HIGH,
            source_ip=_rand_ip(INTERNAL_IPS),
            dest_ip=_rand_ip(KNOWN_BAD_IPS),
            user=random.choice(["svc-payments", "svc-billing"]),
            namespace="demo-workloads",
            pod_name=pod,
            bytes_transferred=random.randint(50_000_000, 500_000_000),
            is_known_bad_ip=True,
            scenario_tag=ScenarioTag.DATA_EXFILTRATION,
            metadata={"technique": "T1041 - Exfiltration Over C2 Channel"},
        )


def privilege_escalation_scenario() -> Iterator[SecurityEvent]:
    """Container escape / privilege escalation attempt."""
    pod = random.choice(DEMO_PODS)
    yield SecurityEvent(
        event_type=EventType.PRIVILEGE_ESCALATION,
        severity_hint=Severity.CRITICAL,
        source_ip=_rand_ip(INTERNAL_IPS),
        user="root",
        namespace="demo-workloads",
        pod_name=pod,
        process_name=random.choice(["chroot", "nsenter", "setuid-helper"]),
        process_spawn_rate_last_1m=round(random.uniform(2.0, 5.0), 2),
        scenario_tag=ScenarioTag.PRIVILEGE_ESCALATION,
        metadata={"technique": "T1611 - Escape to Host"},
    )


def port_scan_scenario() -> Iterator[SecurityEvent]:
    """Internal reconnaissance sweeping many ports on one host."""
    attacker_ip = _rand_ip(INTERNAL_IPS)
    for _ in range(random.randint(1, 2)):
        yield SecurityEvent(
            event_type=EventType.PORT_SCAN,
            severity_hint=Severity.MEDIUM,
            source_ip=attacker_ip,
            dest_ip=_rand_ip(INTERNAL_IPS),
            namespace="demo-workloads",
            distinct_ports_last_1m=random.randint(25, 200),
            scenario_tag=ScenarioTag.PORT_SCAN,
            metadata={"technique": "T1046 - Network Service Discovery"},
        )


SCENARIOS = [
    brute_force_scenario,
    crypto_miner_scenario,
    data_exfiltration_scenario,
    privilege_escalation_scenario,
    port_scan_scenario,
]


def generate_stream(attack_probability: float) -> Iterator[SecurityEvent]:
    """Yield one 'tick' worth of events: usually benign noise, occasionally an attack burst."""
    if random.random() < attack_probability:
        scenario_fn = random.choice(SCENARIOS)
        yield from scenario_fn()
    else:
        yield benign_event()
