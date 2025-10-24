import structlog

from src.engine.analyzer import AnalysisResult
from src.engine.llm_provider import LLMProvider, PolicyResponse

logger = structlog.get_logger(__name__)


class PolicyGenerator:
    """
    Generates intelligent sampling policies using LLM analysis.

    Takes pattern analysis results and uses LLM to generate
    smart sampling policies that balance cost and observability.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_policy(
        self, service_name: str, analysis: AnalysisResult, cost_target: float | None = None
    ) -> PolicyResponse:
        """
        Generate sampling policy from analysis results.

        Args:
            service_name: Name of service
            analysis: Pattern analysis results
            cost_target: Optional daily cost target in dollars

        Returns:
            PolicyResponse with sampling rates and reasoning
        """
        prompt = self._build_prompt(service_name, analysis, cost_target)

        logger.info(
            "Generating policy",
            service=service_name,
            patterns=analysis.summary["unique_patterns"],
            anomalies=analysis.summary["anomalies_detected"],
        )

        try:
            policy = await self.llm_provider.generate_policy(prompt)

            policy = self._validate_and_fix_policy(policy)

            logger.info(
                "Policy generated",
                service=service_name,
                global_rate=policy.global_rate,
                model=policy.model,
            )

            return policy

        except Exception as e:
            logger.error("Policy generation failed", service=service_name, error=str(e))
            raise

    def _build_prompt(self, service_name: str, analysis: AnalysisResult, cost_target: float | None) -> str:
        """Build prompt for LLM policy generation."""
        summary = analysis.summary

        clusters_info = "\n".join(
            [
                f"- Pattern {i+1}: '{pattern['message'][:80]}...' "
                f"(count: {pattern['count']}, signature: {pattern['signature'][:8]}...)"
                for i, pattern in enumerate(summary["top_patterns"][:10])
            ]
        )

        anomalies_info = "\n".join(
            [f"- [{a.severity.upper()}] {a.anomaly_type}: {a.message}" for a in analysis.anomalies[:5]]
        )

        cost_section = (
            f"\nCost Target: ${cost_target}/day\nCurrent volume: {summary['total_logs']} logs/hour"
            if cost_target
            else "\nCost Target: No specific target, optimize for value"
        )

        prompt = f"""
Analyze these log patterns and generate an intelligent sampling policy.

Service: {service_name}
Total Logs Analyzed: {summary['total_logs']}
Unique Patterns: {summary['unique_patterns']}
Clusters Found: {summary['clusters_found']}
Anomalies Detected: {summary['anomalies_detected']}
Error Rate: {summary['error_rate']:.1%}
{cost_section}

Severity Distribution:
{self._format_severity_dist(summary['severity_distribution'])}

Top Patterns (by frequency):
{clusters_info or 'None'}

Anomalies Detected:
{anomalies_info or 'None detected'}

Generate a JSON sampling policy with this structure:
{{
  "global_rate": 0.0-1.0,
  "severity_rates": {{
    "DEBUG": 0.0-1.0,
    "INFO": 0.0-1.0,
    "WARNING": 0.0-1.0,
    "ERROR": 1.0,
    "CRITICAL": 1.0
  }},
  "pattern_rates": {{
    "pattern_signature": 0.0-1.0
  }},
  "anomaly_boost": 1.0-10.0,
  "reasoning": "Explain your policy decisions"
}}

Consider:
1. Which patterns are noisy/repetitive vs valuable signals?
2. What sampling rates achieve cost target while maintaining observability?
3. Should any high-volume patterns be sampled more aggressively?
4. How should we boost sampling during detected anomalies?

REMEMBER: ERROR and CRITICAL must ALWAYS be 1.0 (100% sampling)
"""
        return prompt

    def _format_severity_dist(self, severity_dist: dict) -> str:
        """Format severity distribution for prompt."""
        if not severity_dist:
            return "No data"

        return "\n".join([f"  {severity}: {count} logs" for severity, count in severity_dist.items()])

    def _validate_and_fix_policy(self, policy: PolicyResponse) -> PolicyResponse:
        """
        Validate policy and fix any issues.

        Ensures ERROR and CRITICAL are always 1.0 (safety check).
        """
        policy.severity_rates["ERROR"] = 1.0
        policy.severity_rates["CRITICAL"] = 1.0

        if policy.global_rate < 0.0:
            policy.global_rate = 0.0
        if policy.global_rate > 1.0:
            policy.global_rate = 1.0

        if policy.anomaly_boost < 1.0:
            policy.anomaly_boost = 1.0

        for pattern_sig, rate in policy.pattern_rates.items():
            if rate < 0.0:
                policy.pattern_rates[pattern_sig] = 0.0
            if rate > 1.0:
                policy.pattern_rates[pattern_sig] = 1.0

        return policy

