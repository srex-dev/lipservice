from datetime import datetime

import pytest

from src.engine.analyzer import AnalysisResult, PatternAnalysis
from src.engine.llm_provider import PolicyResponse, RuleBasedProvider
from src.engine.pattern_analyzer import PatternCluster
from src.engine.policy_generator import PolicyGenerator


@pytest.fixture
def sample_analysis():
    """Create sample analysis results for testing."""
    clusters = [
        PatternCluster(
            cluster_id=0,
            size=10,
            total_count=1000,
            representative_message="User logged in",
            signature="abc123",
            severity_distribution={"INFO": 950, "WARNING": 50},
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        ),
        PatternCluster(
            cluster_id=1,
            size=5,
            total_count=50,
            representative_message="Payment processed",
            signature="def456",
            severity_distribution={"INFO": 45, "ERROR": 5},
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        ),
    ]

    pattern_analysis = PatternAnalysis(
        clusters=clusters, noise_count=0, total_unique_patterns=15, total_logs=1050
    )

    summary = {
        "total_logs": 1050,
        "unique_patterns": 15,
        "clusters_found": 2,
        "anomalies_detected": 1,
        "high_severity_anomalies": 0,
        "severity_distribution": {"INFO": 995, "WARNING": 50, "ERROR": 5},
        "error_rate": 0.005,
        "top_patterns": [
            {"message": "User logged in", "count": 1000, "signature": "abc123"},
            {"message": "Payment processed", "count": 50, "signature": "def456"},
        ],
    }

    return AnalysisResult(pattern_analysis=pattern_analysis, anomalies=[], summary=summary)


@pytest.mark.asyncio
async def test_policy_generator_with_rule_based_provider(sample_analysis):
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis)

    assert policy is not None
    assert policy.global_rate >= 0.0
    assert policy.global_rate <= 1.0
    assert policy.model == "rule-based"


@pytest.mark.asyncio
async def test_policy_generator_enforces_error_rates(sample_analysis):
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis)

    assert policy.severity_rates["ERROR"] == 1.0
    assert policy.severity_rates["CRITICAL"] == 1.0


@pytest.mark.asyncio
async def test_policy_generator_includes_reasoning(sample_analysis):
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis)

    assert policy.reasoning is not None
    assert len(policy.reasoning) > 0


@pytest.mark.asyncio
async def test_policy_generator_with_cost_target(sample_analysis):
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis, cost_target=100.0)

    assert policy is not None


@pytest.mark.parametrize(
    "error_rate,expected_min_error_sample",
    [
        (0.001, 1.0),  # Low error rate
        (0.05, 1.0),  # Medium error rate
        (0.2, 1.0),  # High error rate
    ],
)
@pytest.mark.asyncio
async def test_policy_always_samples_errors(sample_analysis, error_rate, expected_min_error_sample):
    sample_analysis.summary["error_rate"] = error_rate

    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis)

    assert policy.severity_rates["ERROR"] >= expected_min_error_sample
    assert policy.severity_rates["CRITICAL"] >= expected_min_error_sample


@pytest.mark.asyncio
async def test_policy_validation_fixes_invalid_rates(sample_analysis):
    """Test that policy validation ensures all rates are in valid range."""
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    policy = await generator.generate_policy("test-service", sample_analysis)

    assert 0.0 <= policy.global_rate <= 1.0
    assert policy.anomaly_boost >= 1.0

    for severity, rate in policy.severity_rates.items():
        assert 0.0 <= rate <= 1.0, f"Invalid rate for {severity}: {rate}"


def test_prompt_building_includes_key_info(sample_analysis):
    """Test that prompt includes essential analysis information."""
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    prompt = generator._build_prompt("test-service", sample_analysis, None)

    assert "test-service" in prompt
    assert str(sample_analysis.summary["total_logs"]) in prompt
    assert str(sample_analysis.summary["unique_patterns"]) in prompt
    assert str(sample_analysis.summary["error_rate"]) in prompt or "0.0%" in prompt


def test_prompt_includes_cost_target_when_provided(sample_analysis):
    provider = RuleBasedProvider()
    generator = PolicyGenerator(provider)

    prompt_with_cost = generator._build_prompt("test-service", sample_analysis, 100.0)
    prompt_without_cost = generator._build_prompt("test-service", sample_analysis, None)

    assert "$100" in prompt_with_cost or "100" in prompt_with_cost
    assert "Cost Target:" in prompt_with_cost
    assert "No specific target" in prompt_without_cost or "optimize for value" in prompt_without_cost.lower()

