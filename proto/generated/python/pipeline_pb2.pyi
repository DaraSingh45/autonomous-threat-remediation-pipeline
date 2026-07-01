from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ThreatDetection(_message.Message):
    __slots__ = ("event_id", "detection_id", "event_timestamp_ms", "detected_at_ms", "detection_source", "rule_name", "anomaly_score", "severity", "entity_type", "entity_id", "namespace", "event_type", "raw_event_json")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    DETECTION_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    DETECTION_SOURCE_FIELD_NUMBER: _ClassVar[int]
    RULE_NAME_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_SCORE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RAW_EVENT_JSON_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    detection_id: str
    event_timestamp_ms: int
    detected_at_ms: int
    detection_source: str
    rule_name: str
    anomaly_score: float
    severity: str
    entity_type: str
    entity_id: str
    namespace: str
    event_type: str
    raw_event_json: str
    def __init__(self, event_id: _Optional[str] = ..., detection_id: _Optional[str] = ..., event_timestamp_ms: _Optional[int] = ..., detected_at_ms: _Optional[int] = ..., detection_source: _Optional[str] = ..., rule_name: _Optional[str] = ..., anomaly_score: _Optional[float] = ..., severity: _Optional[str] = ..., entity_type: _Optional[str] = ..., entity_id: _Optional[str] = ..., namespace: _Optional[str] = ..., event_type: _Optional[str] = ..., raw_event_json: _Optional[str] = ...) -> None: ...

class DecisionResponse(_message.Message):
    __slots__ = ("decision_id", "approved", "action", "reasoning", "autonomous", "decided_at_ms", "remediation_success", "remediation_details", "remediation_id")
    DECISION_ID_FIELD_NUMBER: _ClassVar[int]
    APPROVED_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    AUTONOMOUS_FIELD_NUMBER: _ClassVar[int]
    DECIDED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    REMEDIATION_SUCCESS_FIELD_NUMBER: _ClassVar[int]
    REMEDIATION_DETAILS_FIELD_NUMBER: _ClassVar[int]
    REMEDIATION_ID_FIELD_NUMBER: _ClassVar[int]
    decision_id: str
    approved: bool
    action: str
    reasoning: str
    autonomous: bool
    decided_at_ms: int
    remediation_success: bool
    remediation_details: str
    remediation_id: str
    def __init__(self, decision_id: _Optional[str] = ..., approved: _Optional[bool] = ..., action: _Optional[str] = ..., reasoning: _Optional[str] = ..., autonomous: _Optional[bool] = ..., decided_at_ms: _Optional[int] = ..., remediation_success: _Optional[bool] = ..., remediation_details: _Optional[str] = ..., remediation_id: _Optional[str] = ...) -> None: ...

class RemediationRequest(_message.Message):
    __slots__ = ("decision_id", "event_id", "detection_id", "action", "entity_type", "entity_id", "namespace", "severity", "reasoning")
    DECISION_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    DETECTION_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    decision_id: str
    event_id: str
    detection_id: str
    action: str
    entity_type: str
    entity_id: str
    namespace: str
    severity: str
    reasoning: str
    def __init__(self, decision_id: _Optional[str] = ..., event_id: _Optional[str] = ..., detection_id: _Optional[str] = ..., action: _Optional[str] = ..., entity_type: _Optional[str] = ..., entity_id: _Optional[str] = ..., namespace: _Optional[str] = ..., severity: _Optional[str] = ..., reasoning: _Optional[str] = ...) -> None: ...

class RemediationResponse(_message.Message):
    __slots__ = ("remediation_id", "success", "details", "remediation_started_ms", "completed_at_ms", "mode")
    REMEDIATION_ID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    REMEDIATION_STARTED_MS_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    remediation_id: str
    success: bool
    details: str
    remediation_started_ms: int
    completed_at_ms: int
    mode: str
    def __init__(self, remediation_id: _Optional[str] = ..., success: _Optional[bool] = ..., details: _Optional[str] = ..., remediation_started_ms: _Optional[int] = ..., completed_at_ms: _Optional[int] = ..., mode: _Optional[str] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
