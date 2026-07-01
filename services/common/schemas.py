from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    FAILED_LOGIN = "failed_login"
    PROCESS_SPAWN = "process_spawn"
    NETWORK_EGRESS = "network_egress"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PORT_SCAN = "port_scan"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScenarioTag(str, Enum):
    BENIGN = "benign"
    BRUTE_FORCE = "brute_force"
    CRYPTO_MINER = "crypto_miner"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PORT_SCAN = "port_scan"


class SecurityEvent(BaseModel):
    """A single synthetic telemetry record produced onto Kafka."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    event_type: EventType
    severity_hint: Severity = Severity.INFO

    source_ip: str
    dest_ip: Optional[str] = None
    user: Optional[str] = None
    namespace: str = "demo-workloads"
    pod_name: Optional[str] = None
    process_name: Optional[str] = None

    bytes_transferred: int = 0
    login_attempts_last_5m: int = 0
    process_spawn_rate_last_1m: float = 0.0
    distinct_ports_last_1m: int = 0
    is_known_bad_ip: bool = False

    # Only used offline to measure detector precision/recall in tests &
    # notebooks - the detection engine intentionally never reads this field
    # when deciding whether to flag an event (that would be cheating).
    scenario_tag: ScenarioTag = ScenarioTag.BENIGN

    metadata: dict = Field(default_factory=dict)


class AuditRecord(BaseModel):
    """Full lifecycle record persisted by the Audit Service."""

    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    detection_id: str
    decision_id: str
    remediation_id: Optional[str] = None

    entity_type: str
    entity_id: str
    namespace: Optional[str] = None
    severity: str
    event_type: str

    action: str
    mode: str  # "autonomous" | "manual_simulated"
    detection_source: str
    rule_name: Optional[str] = None
    anomaly_score: Optional[float] = None

    event_timestamp_ms: int
    detected_at_ms: int
    decided_at_ms: int
    remediation_started_ms: Optional[int] = None
    completed_at_ms: Optional[int] = None

    mttd_ms: Optional[int] = None  # detected_at_ms - event_timestamp_ms
    mttr_ms: Optional[int] = None  # completed_at_ms - detected_at_ms

    success: bool
    details: str
    raw_event: dict = Field(default_factory=dict)
