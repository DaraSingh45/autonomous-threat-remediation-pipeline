import time

from services.decision_engine.policy import DedupCache, decide


def test_low_severity_results_in_monitor_only():
    dedup = DedupCache(cooldown_seconds=60)
    decision = decide("pod", "low", dedup)
    assert decision.action == "monitor"
    assert decision.approved is False


def test_high_severity_on_pod_triggers_isolate():
    dedup = DedupCache(cooldown_seconds=60)
    decision = decide("pod", "high", dedup)
    assert decision.action == "isolate_pod"
    assert decision.approved is True


def test_critical_severity_on_user_triggers_revoke():
    dedup = DedupCache(cooldown_seconds=60)
    decision = decide("user", "critical", dedup)
    assert decision.action == "revoke_credential"
    assert decision.approved is True


def test_unknown_entity_type_is_not_actionable():
    dedup = DedupCache(cooldown_seconds=60)
    decision = decide("host", "critical", dedup)
    assert decision.approved is False
    assert decision.action == "monitor"


def test_dedup_cache_suppresses_within_cooldown():
    dedup = DedupCache(cooldown_seconds=60)
    assert dedup.should_suppress("pod:my-pod") is False
    dedup.mark_actioned("pod:my-pod")
    assert dedup.should_suppress("pod:my-pod") is True


def test_dedup_cache_allows_after_cooldown_expires():
    dedup = DedupCache(cooldown_seconds=0.1)
    dedup.mark_actioned("pod:my-pod")
    assert dedup.should_suppress("pod:my-pod") is True
    time.sleep(0.15)
    assert dedup.should_suppress("pod:my-pod") is False


def test_dedup_cache_is_per_entity():
    dedup = DedupCache(cooldown_seconds=60)
    dedup.mark_actioned("pod:pod-a")
    assert dedup.should_suppress("pod:pod-a") is True
    assert dedup.should_suppress("pod:pod-b") is False
