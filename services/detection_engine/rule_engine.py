from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services.common.schemas import EventType, SecurityEvent, Severity

SUSPICIOUS_PROCESSES = {"xmrig", "kinsing", "cryptominer.sh", "ncat", "masscan"}

BRUTE_FORCE_THRESHOLD = 5
LARGE_EXFIL_BYTES = 25_000_000  # 25 MB
PORT_SCAN_THRESHOLD = 20


@dataclass
class RuleMatch:
    rule_name: str
    severity: Severity


def evaluate_rules(event: SecurityEvent) -> Optional[RuleMatch]:
    """Return the highest-severity rule match for this event, or None."""

    matches: list[RuleMatch] = []

    # R1 - Brute force login
    if event.event_type == EventType.FAILED_LOGIN and event.login_attempts_last_5m >= BRUTE_FORCE_THRESHOLD:
        matches.append(RuleMatch("brute_force_login_threshold", Severity.HIGH))

    # R2 - Known-bad network destination
    if event.event_type == EventType.NETWORK_EGRESS and event.is_known_bad_ip:
        matches.append(RuleMatch("known_bad_destination_ip", Severity.CRITICAL))

    # R3 - Suspicious / blocklisted process
    if event.process_name and event.process_name.lower() in SUSPICIOUS_PROCESSES:
        matches.append(RuleMatch("blocklisted_process_spawn", Severity.CRITICAL))

    # R4 - Large outbound transfer (possible exfiltration)
    if event.event_type == EventType.NETWORK_EGRESS and event.bytes_transferred >= LARGE_EXFIL_BYTES:
        matches.append(RuleMatch("large_outbound_transfer", Severity.HIGH))

    # R5 - Privilege escalation / container escape indicators
    if event.event_type == EventType.PRIVILEGE_ESCALATION:
        matches.append(RuleMatch("privilege_escalation_attempt", Severity.CRITICAL))

    # R6 - Internal port scan / reconnaissance
    if event.event_type == EventType.PORT_SCAN and event.distinct_ports_last_1m >= PORT_SCAN_THRESHOLD:
        matches.append(RuleMatch("internal_port_scan", Severity.MEDIUM))

    if not matches:
        return None

    severity_rank = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}
    return max(matches, key=lambda m: severity_rank[m.severity])
