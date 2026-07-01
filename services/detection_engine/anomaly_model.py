"""
Isolation Forest anomaly detector.

The rule engine catches known patterns; this catches the "doesn't look
right but doesn't match a signature" case, which is the entire point of
pairing a behavioral model with deterministic rules in a real detection
stack.

Model is trained offline (see train_isolation_forest.py) on a synthetic
"normal" telemetry distribution and shipped as a pickled artifact at
services/detection_engine/models/isolation_forest.pkl. At startup this
module loads that artifact; if it's missing (e.g. a clean checkout without
running the training script) it trains a small model in-process from the
same generator so the service still boots and behaves sensibly.
"""

from __future__ import annotations

import math
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from services.common.schemas import SecurityEvent, Severity

MODEL_PATH = Path(os.environ.get("ANOMALY_MODEL_PATH", Path(__file__).parent / "models" / "isolation_forest.pkl"))

# decision_function() scores: more negative == more anomalous.
# These thresholds were picked by inspecting the score distribution over the
# synthetic training set (see train_isolation_forest.py's printed summary):
# 0.0% of pure-benign training data scores below -0.06, and ~1.3% scores
# below -0.015, giving a deliberately low false-positive budget for a demo
# with a fairly small/simple feature set.
ANOMALY_SCORE_HIGH = -0.06
ANOMALY_SCORE_MEDIUM = -0.015


@dataclass
class AnomalyResult:
    score: float
    is_anomalous: bool
    severity: Optional[Severity]


def extract_features(event: SecurityEvent) -> np.ndarray:
    """Turn a SecurityEvent into the fixed-length numeric feature vector the
    model was trained on. Order matters and must match train_isolation_forest.py.
    """
    hour = ((event.timestamp_ms // 1000) // 3600) % 24
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    return np.array(
        [
            event.login_attempts_last_5m,
            event.process_spawn_rate_last_1m,
            math.log1p(event.bytes_transferred),
            event.distinct_ports_last_1m,
            hour_sin,
            hour_cos,
            1.0 if event.is_known_bad_ip else 0.0,
        ],
        dtype=float,
    ).reshape(1, -1)


class AnomalyDetector:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.model = self._load_or_train()

    def _load_or_train(self):
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                return pickle.load(f)

        # Fallback: train a small model in-process so the service still
        # works on a fresh checkout without requiring the training script
        # to be run first. Not used when the shipped .pkl is present.
        from services.detection_engine.train_isolation_forest import build_training_matrix
        from sklearn.ensemble import IsolationForest

        X = build_training_matrix(n_samples=4000, seed=42)
        model = IsolationForest(n_estimators=150, contamination=0.03, random_state=42)
        model.fit(X)
        return model

    def score(self, event: SecurityEvent) -> AnomalyResult:
        features = extract_features(event)
        raw_score = float(self.model.decision_function(features)[0])

        if raw_score <= ANOMALY_SCORE_HIGH:
            return AnomalyResult(score=raw_score, is_anomalous=True, severity=Severity.HIGH)
        if raw_score <= ANOMALY_SCORE_MEDIUM:
            return AnomalyResult(score=raw_score, is_anomalous=True, severity=Severity.MEDIUM)
        return AnomalyResult(score=raw_score, is_anomalous=False, severity=None)
