import numpy as np

from services.common.schemas import EventType, SecurityEvent
from services.detection_engine.anomaly_model import AnomalyDetector, extract_features
from services.detection_engine.train_isolation_forest import build_training_matrix


def test_feature_vector_shape():
    event = SecurityEvent(event_type=EventType.PROCESS_SPAWN, source_ip="10.0.1.10")
    features = extract_features(event)
    assert features.shape == (1, 7)


def test_training_matrix_shape_and_no_nans():
    X = build_training_matrix(n_samples=200, seed=1)
    assert X.shape == (200, 7)
    assert not np.isnan(X).any()


def test_benign_event_is_rarely_flagged():
    detector = AnomalyDetector()
    flagged = 0
    for _ in range(50):
        event = SecurityEvent(
            event_type=EventType.PROCESS_SPAWN,
            source_ip="10.0.1.10",
            process_name="python3",
            process_spawn_rate_last_1m=0.6,
            login_attempts_last_5m=0,
            bytes_transferred=15_000,
        )
        result = detector.score(event)
        if result.is_anomalous:
            flagged += 1
    # Should be a small minority - this is a false-positive-rate sanity check,
    # not a precise statistical claim.
    assert flagged <= 5


def test_extreme_brute_force_pattern_is_flagged_anomalous():
    detector = AnomalyDetector()
    event = SecurityEvent(
        event_type=EventType.FAILED_LOGIN,
        source_ip="45.155.205.233",
        user="alice",
        login_attempts_last_5m=14,
        is_known_bad_ip=True,
    )
    result = detector.score(event)
    assert result.is_anomalous is True
