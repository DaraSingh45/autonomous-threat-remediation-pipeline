from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

AUTONOMOUS_MODE = os.environ.get("AUTONOMOUS_MODE", "true").lower() == "true"
SIMULATED_MANUAL_TRIAGE_SECONDS = float(os.environ.get("SIMULATED_MANUAL_TRIAGE_SECONDS", "20"))
REMEDIATION_COOLDOWN_SECONDS = float(os.environ.get("REMEDIATION_COOLDOWN_SECONDS", "300"))

# Only these severities warrant an autonomous action at all; anything below
# is logged as "monitor" so the audit trail still shows the pipeline saw it.
ACTIONABLE_SEVERITIES = {"high", "critical"}

ACTION_BY_ENTITY = {
    "pod": "isolate_pod",
    "user": "revoke_credential",
}


@dataclass
class Decision:
    action: str          # "isolate_pod" | "revoke_credential" | "monitor" | "none"
    approved: bool        # whether a remediation call should be made
    reasoning: str
    autonomous: bool
    simulated_delay_s: float = 0.0


class DedupCache:
    """Tracks the last time we remediated a given entity, to avoid
    remediation storms when telemetry keeps re-triggering for the same
    already-quarantined entity."""

    def __init__(self, cooldown_seconds: float = REMEDIATION_COOLDOWN_SECONDS):
        self._cooldown = cooldown_seconds
        self._last_action: dict[str, float] = {}
        self._lock = threading.Lock()

    def should_suppress(self, entity_key: str) -> bool:
        with self._lock:
            last = self._last_action.get(entity_key)
            return last is not None and (time.time() - last) < self._cooldown

    def mark_actioned(self, entity_key: str) -> None:
        with self._lock:
            self._last_action[entity_key] = time.time()


def decide(entity_type: str, severity: str, dedup: DedupCache) -> Decision:
    entity_action = ACTION_BY_ENTITY.get(entity_type)

    if severity not in ACTIONABLE_SEVERITIES or entity_action is None:
        return Decision(
            action="monitor",
            approved=False,
            reasoning=f"severity={severity} entity_type={entity_type} below actionable policy threshold",
            autonomous=AUTONOMOUS_MODE,
        )

    return Decision(
        action=entity_action,
        approved=True,
        reasoning=f"severity={severity} on entity_type={entity_type} meets autonomous remediation policy",
        autonomous=AUTONOMOUS_MODE,
        simulated_delay_s=0.0 if AUTONOMOUS_MODE else SIMULATED_MANUAL_TRIAGE_SECONDS,
    )
