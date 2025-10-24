import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

import structlog
from anthropic import Anthropic
from openai import OpenAI

logger = structlog.get_logger(__name__)


@dataclass
class PolicyResponse:
    """Response from LLM policy generation."""

    global_rate: float
    severity_rates: dict[str, float]
    pattern_rates: dict[str, float]
    anomaly_boost: float
    reasoning: str
    model: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_policy(self, prompt: str) -> PolicyResponse:
        """Generate sampling policy from prompt."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get LLM model identifier."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider for policy generation."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate_policy(self, prompt: str) -> PolicyResponse:
        """Generate policy using OpenAI."""
        logger.info("Generating policy with OpenAI", model=self.model)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in log management and observability.
Your task is to generate intelligent sampling policies that balance cost, observability, and debugging needs.

CRITICAL RULES:
1. ALWAYS keep ERROR and CRITICAL logs at 100% (1.0)
2. Sample repetitive INFO/DEBUG logs aggressively (0.01-0.1)
3. Keep first occurrences of new patterns at 100%
4. Increase sampling during anomalies (anomaly_boost: 2.0-5.0)
5. Balance cost constraints with observability needs""",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            content = response.choices[0].message.content
            policy_data = json.loads(content)

            policy_data["severity_rates"]["ERROR"] = 1.0
            policy_data["severity_rates"]["CRITICAL"] = 1.0

            logger.info("Policy generated successfully", model=self.model)

            return PolicyResponse(
                global_rate=policy_data.get("global_rate", 1.0),
                severity_rates=policy_data.get("severity_rates", {}),
                pattern_rates=policy_data.get("pattern_rates", {}),
                anomaly_boost=policy_data.get("anomaly_boost", 2.0),
                reasoning=policy_data.get("reasoning", ""),
                model=self.model,
            )

        except Exception as e:
            logger.error("OpenAI policy generation failed", error=str(e))
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) provider for policy generation."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def generate_policy(self, prompt: str) -> PolicyResponse:
        """Generate policy using Anthropic Claude."""
        logger.info("Generating policy with Anthropic", model=self.model)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system="""You are an expert in log management and observability.
Generate intelligent sampling policies that balance cost and observability.

CRITICAL RULES:
1. ALWAYS keep ERROR and CRITICAL logs at 100% (1.0)
2. Sample repetitive INFO/DEBUG logs aggressively
3. Increase sampling during anomalies
4. Return valid JSON only""",
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            content_json = content
            if "```json" in content:
                content_json = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content_json = content.split("```")[1].split("```")[0].strip()

            policy_data = json.loads(content_json)

            policy_data["severity_rates"]["ERROR"] = 1.0
            policy_data["severity_rates"]["CRITICAL"] = 1.0

            logger.info("Policy generated successfully", model=self.model)

            return PolicyResponse(
                global_rate=policy_data.get("global_rate", 1.0),
                severity_rates=policy_data.get("severity_rates", {}),
                pattern_rates=policy_data.get("pattern_rates", {}),
                anomaly_boost=policy_data.get("anomaly_boost", 2.0),
                reasoning=policy_data.get("reasoning", ""),
                model=self.model,
            )

        except Exception as e:
            logger.error("Anthropic policy generation failed", error=str(e))
            raise


class RuleBasedProvider(LLMProvider):
    """Fallback rule-based provider (no LLM required)."""

    def __init__(self):
        pass

    async def generate_policy(self, prompt: str) -> PolicyResponse:
        """Generate conservative rule-based policy."""
        logger.info("Generating rule-based policy (fallback)")

        return PolicyResponse(
            global_rate=1.0,
            severity_rates={
                "DEBUG": 0.05,
                "INFO": 0.2,
                "WARNING": 0.5,
                "ERROR": 1.0,
                "CRITICAL": 1.0,
            },
            pattern_rates={},
            anomaly_boost=3.0,
            reasoning="Conservative rule-based policy - LLM unavailable or disabled",
            model="rule-based",
        )

    def get_model_name(self) -> str:
        return "rule-based"

