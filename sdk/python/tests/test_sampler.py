"""Tests for adaptive sampler."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lipservice.client import LipServiceClient
from lipservice.models import SamplingPolicy
from lipservice.sampler import AdaptiveSampler


@pytest.fixture
def mock_client():
    """Create mock LipService client."""
    client = MagicMock(spec=LipServiceClient)
    client.service_name = "test-service"
    client.get_active_policy = AsyncMock(return_value=None)
    client.report_patterns = AsyncMock(return_value=True)
    return client


@pytest.fixture
def sampler(mock_client):
    """Create adaptive sampler with mock client."""
    return AdaptiveSampler(
        client=mock_client,
        policy_refresh_interval=1,
        pattern_report_interval=1,
    )


def test_sampler_initialization(sampler, mock_client):
    """Test sampler initializes correctly."""
    assert sampler.client == mock_client
    assert sampler.policy is None
    assert len(sampler.pattern_stats) == 0


def test_always_sample_errors(sampler):
    """Test that ERROR logs are always sampled."""
    should_sample, sig = sampler.should_sample("Error occurred", "ERROR")
    assert should_sample is True


def test_always_sample_critical(sampler):
    """Test that CRITICAL logs are always sampled."""
    should_sample, sig = sampler.should_sample("Critical failure", "CRITICAL")
    assert should_sample is True


def test_always_sample_fatal(sampler):
    """Test that FATAL logs are always sampled."""
    should_sample, sig = sampler.should_sample("Fatal error", "FATAL")
    assert should_sample is True


def test_sampler_without_policy_samples_all(sampler):
    """Test that without policy, all logs are sampled (fallback)."""
    should_sample, sig = sampler.should_sample("Info message", "INFO")
    # Without policy, fallback is 100%
    assert should_sample is True


def test_sampler_tracks_patterns(sampler):
    """Test that sampler tracks pattern statistics."""
    sampler.should_sample("User logged in", "INFO")
    sampler.should_sample("User logged in", "INFO")
    sampler.should_sample("User logged in", "INFO")

    assert len(sampler.pattern_stats) == 1
    sig = list(sampler.pattern_stats.keys())[0]
    assert sampler.pattern_stats[sig]["count"] == 3


def test_sampler_respects_severity_rates():
    """Test that sampler respects severity-based sampling rates."""
    mock_client = MagicMock(spec=LipServiceClient)
    mock_client.service_name = "test-service"

    sampler = AdaptiveSampler(client=mock_client)

    # Set a policy with low INFO rate
    sampler.policy = SamplingPolicy(
        version=1,
        global_rate=0.5,
        severity_rates={"INFO": 0.0, "ERROR": 1.0},  # 0% INFO, 100% ERROR
        pattern_rates={},
        anomaly_boost=2.0,
    )

    # ERROR should always sample
    should_sample, _ = sampler.should_sample("Error happened", "ERROR")
    assert should_sample is True

    # INFO should never sample (with rate 0.0)
    # Run multiple times to ensure consistency
    samples = [sampler.should_sample("Info message", "INFO")[0] for _ in range(100)]
    assert all(s is False for s in samples)


def test_sampler_respects_pattern_rates():
    """Test that pattern-specific rates override severity rates."""
    mock_client = MagicMock(spec=LipServiceClient)
    mock_client.service_name = "test-service"

    sampler = AdaptiveSampler(client=mock_client)

    # Get signature for our test message
    from lipservice.signature import compute_signature

    message = "User logged in"
    sig = compute_signature(message)

    # Set policy with pattern-specific rate
    sampler.policy = SamplingPolicy(
        version=1,
        global_rate=0.5,
        severity_rates={"INFO": 1.0},  # 100% INFO normally
        pattern_rates={sig: 0.0},  # But 0% for this specific pattern
        anomaly_boost=2.0,
    )

    # Should use pattern rate (0.0) not severity rate (1.0)
    samples = [sampler.should_sample(message, "INFO")[0] for _ in range(100)]
    assert all(s is False for s in samples)


@pytest.mark.asyncio
async def test_sampler_starts_and_stops(sampler):
    """Test sampler lifecycle."""
    await sampler.start()
    assert sampler._running is True

    await sampler.stop()
    assert sampler._running is False


@pytest.mark.asyncio
async def test_sampler_fetches_policy_on_start(mock_client):
    """Test that sampler fetches policy when started."""
    policy = SamplingPolicy(
        version=1,
        global_rate=0.5,
        severity_rates={},
        pattern_rates={},
        anomaly_boost=2.0,
    )
    mock_client.get_active_policy = AsyncMock(return_value=policy)

    sampler = AdaptiveSampler(client=mock_client)
    await sampler.start()

    assert sampler.policy == policy
    mock_client.get_active_policy.assert_called_once()

    await sampler.stop()


def test_sampler_get_stats(sampler):
    """Test get_stats returns current statistics."""
    sampler.should_sample("Test message", "INFO")
    sampler.should_sample("Test message", "INFO")

    stats = sampler.get_stats()

    assert "policy_version" in stats
    assert "patterns_tracked" in stats
    assert "total_logs_seen" in stats
    assert stats["patterns_tracked"] == 1
    assert stats["total_logs_seen"] == 2


def test_sampler_max_cache_size(mock_client):
    """Test that sampler respects max cache size."""
    sampler = AdaptiveSampler(client=mock_client, max_pattern_cache_size=10)

    # Add 15 different patterns
    for i in range(15):
        sampler.should_sample(f"Unique message {i}", "INFO")

    # Should not exceed max cache size
    assert len(sampler.pattern_stats) <= 10

