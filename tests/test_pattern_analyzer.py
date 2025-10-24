from datetime import datetime, timedelta

import pytest

from src.engine.pattern_analyzer import LogEntry, PatternAnalyzer


@pytest.fixture
def sample_logs():
    """Create sample log entries for testing."""
    now = datetime.now()
    return [
        LogEntry("User 123 logged in", "INFO", now, "api"),
        LogEntry("User 456 logged in", "INFO", now + timedelta(seconds=1), "api"),
        LogEntry("User 789 logged in", "INFO", now + timedelta(seconds=2), "api"),
        LogEntry("Payment $99.99 processed", "INFO", now + timedelta(seconds=3), "api"),
        LogEntry("Payment $49.99 processed", "INFO", now + timedelta(seconds=4), "api"),
        LogEntry("Database connection failed", "ERROR", now + timedelta(seconds=5), "api"),
        LogEntry("Database connection timeout", "ERROR", now + timedelta(seconds=6), "api"),
    ]


def test_analyzer_groups_similar_logs(sample_logs):
    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(sample_logs)

    assert analysis.total_logs == 7
    assert analysis.total_unique_patterns <= 7
    assert len(analysis.clusters) >= 1


def test_analyzer_handles_empty_logs():
    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze([])

    assert analysis.total_logs == 0
    assert analysis.total_unique_patterns == 0
    assert len(analysis.clusters) == 0


def test_analyzer_clusters_login_messages():
    now = datetime.now()
    logs = [
        LogEntry(f"User {i} logged in", "INFO", now + timedelta(seconds=i), "api") for i in range(10)
    ]

    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(logs)

    assert analysis.total_logs == 10
    login_clusters = [c for c in analysis.clusters if "logged in" in c.representative_message.lower()]
    assert len(login_clusters) >= 1
    if login_clusters:
        assert login_clusters[0].total_count == 10


def test_analyzer_counts_severity_distribution(sample_logs):
    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(sample_logs)

    total_severity_counts = sum(
        sum(cluster.severity_distribution.values()) for cluster in analysis.clusters
    )
    assert total_severity_counts == len(sample_logs)


def test_analyzer_tracks_first_and_last_seen():
    now = datetime.now()
    logs = [
        LogEntry("Test message", "INFO", now, "api"),
        LogEntry("Test message", "INFO", now + timedelta(hours=1), "api"),
    ]

    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(logs)

    assert len(analysis.clusters) >= 1
    cluster = analysis.clusters[0]
    assert cluster.first_seen == now
    assert cluster.last_seen == now + timedelta(hours=1)


@pytest.mark.parametrize(
    "eps,min_samples",
    [
        (0.3, 2),
        (0.5, 2),
        (0.7, 3),
    ],
)
def test_analyzer_with_different_parameters(sample_logs, eps, min_samples):
    analyzer = PatternAnalyzer(eps=eps, min_samples=min_samples)
    analysis = analyzer.analyze(sample_logs)

    assert analysis.total_logs == len(sample_logs)
    assert len(analysis.clusters) >= 1


def test_analyzer_handles_single_log():
    now = datetime.now()
    logs = [LogEntry("Single log message", "INFO", now, "api")]

    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(logs)

    assert analysis.total_logs == 1
    assert len(analysis.clusters) == 1
    assert analysis.clusters[0].total_count == 1


def test_clusters_sorted_by_count_descending():
    now = datetime.now()
    logs = [
        LogEntry("Frequent message", "INFO", now + timedelta(seconds=i), "api") for i in range(10)
    ] + [LogEntry("Rare message", "INFO", now + timedelta(seconds=i), "api") for i in range(2)]

    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze(logs)

    if len(analysis.clusters) > 1:
        for i in range(len(analysis.clusters) - 1):
            assert analysis.clusters[i].total_count >= analysis.clusters[i + 1].total_count

