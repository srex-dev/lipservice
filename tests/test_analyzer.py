from datetime import datetime, timedelta

import pytest

from src.engine.analyzer import LogAnalyzer
from src.engine.pattern_analyzer import LogEntry


@pytest.fixture
def sample_logs():
    """Create realistic sample logs for testing."""
    now = datetime.now()
    logs = []

    for i in range(50):
        logs.append(LogEntry(f"User {i} logged in", "INFO", now + timedelta(seconds=i), "api"))

    for i in range(10):
        logs.append(LogEntry(f"Payment ${i*10} processed", "INFO", now + timedelta(seconds=50 + i), "api"))

    for i in range(5):
        logs.append(LogEntry("Database connection failed", "ERROR", now + timedelta(seconds=60 + i), "api"))

    return logs


def test_analyzer_complete_workflow(sample_logs):
    analyzer = LogAnalyzer()
    result = analyzer.analyze(sample_logs)

    assert result.pattern_analysis is not None
    assert result.anomalies is not None
    assert result.summary is not None

    assert result.pattern_analysis.total_logs == len(sample_logs)
    assert result.summary["total_logs"] == len(sample_logs)


def test_analyzer_detects_new_patterns():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [
        LogEntry("User logged in", "INFO", now, "api"),
        LogEntry("New error occurred", "ERROR", now + timedelta(seconds=1), "api"),
    ]

    known_sigs = set()
    result = analyzer.analyze(logs, known_signatures=known_sigs)

    new_pattern_anomalies = [a for a in result.anomalies if a.anomaly_type == "new_pattern"]
    assert len(new_pattern_anomalies) >= 1


def test_analyzer_detects_error_surge():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [LogEntry(f"Error {i}", "ERROR", now + timedelta(seconds=i), "api") for i in range(20)] + [
        LogEntry(f"Info {i}", "INFO", now + timedelta(seconds=20 + i), "api") for i in range(5)
    ]

    result = analyzer.analyze(logs)

    error_anomalies = [a for a in result.anomalies if a.anomaly_type == "error_surge"]
    assert len(error_anomalies) >= 1
    if error_anomalies:
        assert error_anomalies[0].severity in ("medium", "high")


def test_analyzer_summary_includes_top_patterns():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [LogEntry(f"Frequent message {i}", "INFO", now + timedelta(seconds=i), "api") for i in range(100)] + [
        LogEntry("Rare message", "INFO", now + timedelta(seconds=100 + i), "api") for i in range(5)
    ]

    result = analyzer.analyze(logs)

    assert "top_patterns" in result.summary
    assert len(result.summary["top_patterns"]) > 0

    top_pattern = result.summary["top_patterns"][0]
    assert "message" in top_pattern
    assert "count" in top_pattern
    assert top_pattern["count"] >= 5


def test_analyzer_calculates_error_rate():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [LogEntry("Error", "ERROR", now + timedelta(seconds=i), "api") for i in range(10)] + [
        LogEntry("Info", "INFO", now + timedelta(seconds=10 + i), "api") for i in range(90)
    ]

    result = analyzer.analyze(logs)

    assert result.summary["error_rate"] == 0.1


def test_analyzer_handles_empty_logs():
    analyzer = LogAnalyzer()
    result = analyzer.analyze([])

    assert result.pattern_analysis.total_logs == 0
    assert result.anomalies == []
    assert result.summary["total_logs"] == 0


def test_analyzer_severity_distribution():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [
        LogEntry("Debug msg", "DEBUG", now, "api"),
        LogEntry("Info msg", "INFO", now + timedelta(seconds=1), "api"),
        LogEntry("Info msg", "INFO", now + timedelta(seconds=2), "api"),
        LogEntry("Warning msg", "WARNING", now + timedelta(seconds=3), "api"),
        LogEntry("Error msg", "ERROR", now + timedelta(seconds=4), "api"),
    ]

    result = analyzer.analyze(logs)

    assert result.summary["severity_distribution"]["DEBUG"] == 1
    assert result.summary["severity_distribution"]["INFO"] == 2
    assert result.summary["severity_distribution"]["WARNING"] == 1
    assert result.summary["severity_distribution"]["ERROR"] == 1


@pytest.mark.parametrize(
    "error_count,total_count,should_detect_surge",
    [
        (25, 100, True),  # 25% errors
        (15, 100, True),  # 15% errors
        (5, 100, False),  # 5% errors - normal
        (0, 100, False),  # No errors
    ],
)
def test_analyzer_error_surge_thresholds(error_count, total_count, should_detect_surge):
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [LogEntry("Error", "ERROR", now + timedelta(seconds=i), "api") for i in range(error_count)] + [
        LogEntry("Info", "INFO", now + timedelta(seconds=error_count + i), "api")
        for i in range(total_count - error_count)
    ]

    result = analyzer.analyze(logs)

    error_surges = [a for a in result.anomalies if a.anomaly_type == "error_surge"]

    if should_detect_surge:
        assert len(error_surges) > 0
    else:
        assert len(error_surges) == 0


def test_analyzer_with_known_signatures_filters_new_patterns():
    analyzer = LogAnalyzer()
    now = datetime.now()

    logs = [
        LogEntry("Known pattern", "INFO", now, "api"),
        LogEntry("New pattern", "INFO", now + timedelta(seconds=1), "api"),
    ]

    from src.engine.signature import compute_signature

    known_sig = compute_signature("Known pattern")
    known_sigs = {known_sig}

    result = analyzer.analyze(logs, known_signatures=known_sigs)

    new_patterns = [a for a in result.anomalies if a.anomaly_type == "new_pattern"]

    assert len(new_patterns) >= 1

