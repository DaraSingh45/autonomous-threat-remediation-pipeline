# Synthetic Threat Scenarios

The event generator (`services/event_generator/scenarios.py`) periodically injects one of five labeled attack bursts among continuous benign background noise. None of these are real attack tools — they only synthesize the telemetry fields a real EDR/CSPM agent would emit for that behavior, so the rest of the pipeline has something realistic to detect and act on.

| Scenario | MITRE ATT&CK | Telemetry pattern | Caught by |
|---|---|---|---|
| Brute force login | [T1110 - Brute Force](https://attack.mitre.org/techniques/T1110/) | 6-14 rapid `failed_login` events against one user from one source IP | Rule `brute_force_login_threshold` (≥5 attempts/5min) **and**, on earlier attempts before that threshold trips, the Isolation Forest — a good example of ML catching a weak early signal before a deterministic rule fires |
| Cryptomining implant | [T1496 - Resource Hijacking](https://attack.mitre.org/techniques/T1496/) | `process_spawn` of a blocklisted binary (`xmrig`, `kinsing`, ...) with elevated spawn rate and a known-bad destination IP | Rule `blocklisted_process_spawn` (critical) |
| Data exfiltration | [T1041 - Exfiltration Over C2 Channel](https://attack.mitre.org/techniques/T1041/) | Large (50-500MB) `network_egress` to a known-bad destination IP | Rule `known_bad_destination_ip` and/or `large_outbound_transfer` |
| Privilege escalation / container escape | [T1611 - Escape to Host](https://attack.mitre.org/techniques/T1611/) | `privilege_escalation` event with a container-escape-adjacent process name | Rule `privilege_escalation_attempt` (critical) |
| Internal port scan | [T1046 - Network Service Discovery](https://attack.mitre.org/techniques/T1046/) | `port_scan` event sweeping 25-200 distinct ports in one minute | Rule `internal_port_scan` (medium) |

## Detection → remediation mapping

| Detected entity | Remediation action | Executed by |
|---|---|---|
| `pod` (process spawn, network egress, privilege escalation events) | `isolate_pod` — label `quarantine=true` + deny-all `NetworkPolicy` | `services/remediation_agent/k8s_actions.py` |
| `user` (failed login events) | `revoke_credential` — mock IAM credential revocation | `services/remediation_agent/iam_client.py` |
| `host` (port scan events, no pod/user context) | Currently policy-classified as `monitor` only (no automated action) | `services/decision_engine/policy.py` |

Every detection below `MIN_SEVERITY_TO_ESCALATE` (default `medium`) is dropped silently by design — it never reaches the Decision Engine, mirroring how a real pipeline would avoid escalating low-confidence noise to an action-taking system.

## Tuning the anomaly model

`services/detection_engine/anomaly_model.py`'s thresholds were calibrated by inspecting the Isolation Forest's `decision_function()` score distribution over 6,000 synthetic benign samples (see the printed summary from `make train-model`):

- 0.0% of pure-benign samples score below `-0.06` → used as the "high" anomaly threshold
- ~1.3% score below `-0.015` → used as the "medium" threshold (an intentionally low false-positive budget for a demo with a small, hand-picked feature set)

If you change the feature set or the synthetic data generator, re-run `make train-model` and re-inspect the printed score distribution before assuming the thresholds still hold.
