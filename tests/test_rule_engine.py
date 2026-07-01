from services.common.schemas import EventType, Severity, SecurityEvent
from services.detection_engine.rule_engine import evaluate_rules


def _event(**overrides) -> SecurityEvent:
    defaults = dict(
        event_type=EventType.PROCESS_SPAWN,
        source_ip="10.0.1.10",
        process_name="python3",
    )
    defaults.update(overrides)
    return SecurityEvent(**defaults)


def test_benign_event_has_no_rule_match():
    event = _event()
    assert evaluate_rules(event) is None


def test_brute_force_threshold_fires_high():
    event = _event(event_type=EventType.FAILED_LOGIN, user="alice", login_attempts_last_5m=5)
    match = evaluate_rules(event)
    assert match is not None
    assert match.rule_name == "brute_force_login_threshold"
    assert match.severity == Severity.HIGH


def test_brute_force_below_threshold_does_not_fire():
    event = _event(event_type=EventType.FAILED_LOGIN, user="alice", login_attempts_last_5m=4)
    assert evaluate_rules(event) is None


def test_known_bad_destination_is_critical():
    event = _event(event_type=EventType.NETWORK_EGRESS, dest_ip="185.220.101.7", is_known_bad_ip=True)
    match = evaluate_rules(event)
    assert match.rule_name == "known_bad_destination_ip"
    assert match.severity == Severity.CRITICAL


def test_blocklisted_process_is_critical():
    event = _event(process_name="xmrig")
    match = evaluate_rules(event)
    assert match.rule_name == "blocklisted_process_spawn"
    assert match.severity == Severity.CRITICAL


def test_large_exfil_transfer_is_high():
    event = _event(event_type=EventType.NETWORK_EGRESS, bytes_transferred=50_000_000)
    match = evaluate_rules(event)
    assert match.rule_name == "large_outbound_transfer"
    assert match.severity == Severity.HIGH


def test_privilege_escalation_is_critical():
    event = _event(event_type=EventType.PRIVILEGE_ESCALATION)
    match = evaluate_rules(event)
    assert match.rule_name == "privilege_escalation_attempt"
    assert match.severity == Severity.CRITICAL


def test_port_scan_threshold_is_medium():
    event = _event(event_type=EventType.PORT_SCAN, distinct_ports_last_1m=25)
    match = evaluate_rules(event)
    assert match.rule_name == "internal_port_scan"
    assert match.severity == Severity.MEDIUM


def test_multiple_matches_returns_highest_severity():
    # Blocklisted process (critical) + would-be brute force fields present but
    # wrong event_type - only the process rule should fire, and critical wins
    # if another medium-severity rule also matched on the same event.
    event = _event(
        event_type=EventType.PORT_SCAN,
        process_name="xmrig",
        distinct_ports_last_1m=30,
    )
    match = evaluate_rules(event)
    assert match.severity == Severity.CRITICAL
