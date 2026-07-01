from __future__ import annotations

import math
import pickle
import random
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_OUT = Path(__file__).parent / "models" / "isolation_forest.pkl"


def build_training_matrix(n_samples: int = 6000, seed: int = 42) -> np.ndarray:
    """Synthesize feature vectors representing normal (benign) traffic.

    Feature order must match anomaly_model.extract_features():
      [login_attempts_5m, process_spawn_rate_1m, log1p(bytes), distinct_ports_1m,
       hour_sin, hour_cos, is_known_bad_ip]
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    rows = []
    for _ in range(n_samples):
        hour = rng.randint(0, 23)
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)

        login_attempts = np_rng.poisson(0.3)
        spawn_rate = max(0.0, np_rng.normal(0.6, 0.4))
        bytes_transferred = int(max(0, np_rng.normal(15_000, 12_000)))
        distinct_ports = np_rng.poisson(1.5)
        is_bad_ip = 0.0  # normal traffic is never to/from a known-bad IP

        rows.append(
            [
                login_attempts,
                spawn_rate,
                math.log1p(bytes_transferred),
                distinct_ports,
                hour_sin,
                hour_cos,
                is_bad_ip,
            ]
        )
    return np.array(rows, dtype=float)


def main():
    X = build_training_matrix(n_samples=6000, seed=42)

    model = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    scores = model.decision_function(X)
    print(f"Trained on {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Score distribution: min={scores.min():.4f} p05={np.percentile(scores, 5):.4f} "
          f"median={np.median(scores):.4f} max={scores.max():.4f}")

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_OUT, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved model to {MODEL_OUT}")


if __name__ == "__main__":
    main()
