import pytest

from src.engine.llm_provider import RuleBasedProvider


@pytest.mark.asyncio
async def test_rule_based_provider_generates_conservative_policy():
    provider = RuleBasedProvider()
    policy = await provider.generate_policy("Test prompt")

    assert policy.global_rate == 1.0
    assert policy.severity_rates["ERROR"] == 1.0
    assert policy.severity_rates["CRITICAL"] == 1.0
    assert policy.severity_rates["DEBUG"] == 0.05
    assert policy.severity_rates["INFO"] == 0.2
    assert policy.anomaly_boost == 3.0
    assert policy.model == "rule-based"


@pytest.mark.asyncio
async def test_rule_based_provider_includes_reasoning():
    provider = RuleBasedProvider()
    policy = await provider.generate_policy("Test prompt")

    assert "rule-based" in policy.reasoning.lower()
    assert len(policy.reasoning) > 10


def test_rule_based_provider_model_name():
    provider = RuleBasedProvider()
    assert provider.get_model_name() == "rule-based"


@pytest.mark.asyncio
async def test_rule_based_provider_is_deterministic():
    provider = RuleBasedProvider()

    policy1 = await provider.generate_policy("Prompt 1")
    policy2 = await provider.generate_policy("Prompt 2")

    assert policy1.global_rate == policy2.global_rate
    assert policy1.severity_rates == policy2.severity_rates
    assert policy1.anomaly_boost == policy2.anomaly_boost

