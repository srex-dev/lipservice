import time

import pytest

from src.engine.anomaly_detector import AnomalyDetector


@pytest.mark.parametrize(
    "current_rate,baseline_rate,should_detect",
    [
        (10.0, 2.0, True),  # 5x spike - should detect
        (6.0, 2.0, True),  # 3x spike - should detect
        (3.0, 2.0, False),  # 1.5x - normal variation
        (2.5, 2.0, False),  # 1.25x - normal variation
        (100.0, 10.0, True),  # 10x spike - definitely detect
    ],
)
def test_detect_rate_anomaly(current_rate, baseline_rate, should_detect):
    detector = AnomalyDetector()
    anomaly = detector.detect_rate_anomaly(current_rate, baseline_rate)

    if should_detect:
        assert anomaly is not None
        assert anomaly.anomaly_type == "rate_spike"
        assert anomaly.current_value == current_rate
        assert anomaly.baseline_value == baseline_rate
    else:
        assert anomaly is None


def test_rate_anomaly_severity_levels():
    detector = AnomalyDetector()

    low = detector.detect_rate_anomaly(4.0, 2.0)  # 2x
    medium = detector.detect_rate_anomaly(6.0, 2.0)  # 3x
    high = detector.detect_rate_anomaly(10.0, 2.0)  # 5x

    assert low.severity == "low"
    assert medium.severity == "medium"
    assert high.severity == "high"


def test_detect_rate_anomaly_with_zero_baseline():
    detector = AnomalyDetector()
    anomaly = detector.detect_rate_anomaly(10.0, 0.0)

    assert anomaly is None


@pytest.mark.parametrize(
    "z_score,threshold,should_detect",
    [
        (4.0, 3.0, True),  # Above threshold
        (3.5, 3.0, True),  # Above threshold
        (2.5, 3.0, False),  # Below threshold
        (1.0, 3.0, False),  # Well below threshold
    ],
)
def test_detect_with_zscore(z_score, threshold, should_detect):
    detector = AnomalyDetector(z_threshold=threshold)

    mean = 10.0
    std = 2.0
    current = mean + (z_score * std)

    values = [mean] * 100

    anomaly = detector.detect_with_zscore(values, current)

    if should_detect:
        assert anomaly is not None
        assert anomaly.anomaly_type == "rate_spike"
    else:
        assert anomaly is None


def test_zscore_detection_with_insufficient_data():
    detector = AnomalyDetector()
    anomaly = detector.detect_with_zscore([10.0], 20.0)

    assert anomaly is None


def test_zscore_detection_with_zero_variance():
    detector = AnomalyDetector()
    values = [10.0] * 100

    anomaly = detector.detect_with_zscore(values, 10.0)

    assert anomaly is None


@pytest.mark.parametrize(
    "current_error_rate,baseline_error_rate,should_detect,expected_severity",
    [
        (10.0, 0.0, True, "high"),  # New errors
        (8.0, 2.0, True, "high"),  # 4x increase
        (6.0, 2.0, True, "medium"),  # 3x increase
        (3.0, 2.0, False, None),  # 1.5x - normal
        (0.0, 0.0, False, None),  # No errors
    ],
)
def test_detect_error_surge(current_error_rate, baseline_error_rate, should_detect, expected_severity):
    detector = AnomalyDetector()
    anomaly = detector.detect_error_surge(current_error_rate, baseline_error_rate, total_logs=1000)

    if should_detect:
        assert anomaly is not None
        assert anomaly.anomaly_type == "error_surge"
        assert anomaly.severity == expected_severity
    else:
        assert anomaly is None


def test_is_new_pattern():
    detector = AnomalyDetector()
    known = {"sig1", "sig2", "sig3"}

    assert detector.is_new_pattern("sig4", known) is True
    assert detector.is_new_pattern("sig1", known) is False
    assert detector.is_new_pattern("sig2", known) is False


def test_update_rate_window():
    detector = AnomalyDetector(window_size=5)

    for i in range(10):
        detector.update_rate_window(float(i))

    assert len(detector.rate_window) == 5
    assert list(detector.rate_window) == [5.0, 6.0, 7.0, 8.0, 9.0]


def test_get_current_rate():
    detector = AnomalyDetector()
    now = time.time()

    for i in range(50):
        detector.update_rate_window(now - i)

    rate = detector.get_current_rate(window_seconds=10)

    assert rate > 0
    assert rate <= 50 / 10


def test_get_current_rate_with_insufficient_data():
    detector = AnomalyDetector()
    rate = detector.get_current_rate()

    assert rate == 0.0


def test_anomaly_confidence_scaling():
    detector = AnomalyDetector()

    low = detector.detect_rate_anomaly(4.0, 2.0)  # 2x
    medium = detector.detect_rate_anomaly(6.0, 2.0)  # 3x
    high = detector.detect_rate_anomaly(20.0, 2.0)  # 10x

    assert low.confidence < medium.confidence < high.confidence


def test_zscore_confidence_calculation():
    detector = AnomalyDetector(z_threshold=3.0)
    values = [10.0] * 100

    anomaly = detector.detect_with_zscore(values, 20.0)

    assert anomaly is not None
    assert 0.0 <= anomaly.confidence <= 1.0

