# Contributing

This started as my (Dara Singh) personal portfolio/learning project, but issues and PRs are welcome if you find bugs or want to extend it.

## Development workflow

```bash
make install    # venv + all service requirements + dev tools
make lint       # ruff
make test       # pytest
```

## Adding a new detection rule

Add a case to `evaluate_rules()` in `services/detection_engine/rule_engine.py` and a corresponding test in `tests/test_rule_engine.py`. Keep rules deterministic and side-effect-free — all of the policy/action logic belongs in `services/decision_engine/policy.py`, not here.

## Adding a new remediation action

1. Add the action name to `ACTION_BY_ENTITY` in `services/decision_engine/policy.py`.
2. Implement the actual execution in `services/remediation_agent/` (either `k8s_actions.py` for cluster actions or a new client module for external systems).
3. Wire the dispatch in `services/remediation_agent/server.py`'s `ExecuteRemediation`.
4. Update `docs/THREAT_SCENARIOS.md`'s mapping table.

## Changing the gRPC contract

Edit `proto/pipeline.proto`, then run `make proto` (or `./scripts/generate_proto.sh`) to regenerate the committed stubs in `proto/generated/python/` before committing.

## Retraining the anomaly model

If you change the feature set in `services/detection_engine/anomaly_model.py`, update `build_training_matrix()` in `train_isolation_forest.py` to match, then run `make train-model` and re-inspect the printed score distribution before assuming the existing thresholds still make sense.
