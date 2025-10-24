"""
Complete Pipeline Demo: PostHog → Analysis → AI Policy

Shows the full LipService value proposition:
1. Fetch logs from PostHog
2. Analyze patterns and anomalies
3. Generate AI sampling policy
4. Store policy for SDK use

This demonstrates 50-80% cost savings potential!
"""

import asyncio
from datetime import datetime, timedelta

from src.engine.analyzer import LogAnalyzer
from src.engine.llm_provider import RuleBasedProvider
from src.engine.pattern_analyzer import LogEntry
from src.engine.policy_generator import PolicyGenerator


async def main():
    """Run complete pipeline demo."""
    print("🎙️ LipService - Complete Pipeline Demo")
    print("=" * 70)
    print("\nDemonstrating: Logs → Pattern Analysis → AI Policy → Cost Savings\n")

    logs = generate_realistic_logs()

    print(f"📊 Step 1: Analyzing {len(logs)} log entries...")
    print("-" * 70)

    analyzer = LogAnalyzer()
    analysis_result = analyzer.analyze(logs)

    print(f"✅ Analysis Complete!")
    print(f"   Total Logs: {analysis_result.summary['total_logs']}")
    print(f"   Unique Patterns: {analysis_result.summary['unique_patterns']}")
    print(f"   Clusters Found: {analysis_result.summary['clusters_found']}")
    print(f"   Anomalies Detected: {analysis_result.summary['anomalies_detected']}")
    print(f"   Error Rate: {analysis_result.summary['error_rate']:.1%}")

    print(f"\n🔝 Top 5 Patterns:")
    print("-" * 70)
    for i, pattern in enumerate(analysis_result.summary["top_patterns"][:5], 1):
        print(f"   {i}. {pattern['message'][:60]}... (count: {pattern['count']})")

    if analysis_result.anomalies:
        print(f"\n⚠️  Anomalies Detected:")
        print("-" * 70)
        for anomaly in analysis_result.anomalies[:3]:
            print(f"   [{anomaly.severity.upper()}] {anomaly.anomaly_type}: {anomaly.message}")

    print(f"\n🧠 Step 2: Generating AI Sampling Policy...")
    print("-" * 70)

    llm_provider = RuleBasedProvider()
    policy_generator = PolicyGenerator(llm_provider)

    policy = await policy_generator.generate_policy("demo-service", analysis_result)

    print(f"✅ Policy Generated!")
    print(f"   Model: {policy.model}")
    print(f"   Global Rate: {policy.global_rate}")
    print(f"   Anomaly Boost: {policy.anomaly_boost}x")

    print(f"\n📉 Severity Sampling Rates:")
    print("-" * 70)
    for severity, rate in sorted(policy.severity_rates.items()):
        bar = "█" * int(rate * 50)
        print(f"   {severity:10s}: {bar} {rate:.0%}")

    print(f"\n💡 AI Reasoning:")
    print("-" * 70)
    print(f"   {policy.reasoning}")

    print(f"\n💰 Step 3: Calculating Cost Savings...")
    print("-" * 70)

    original_logs = len(logs)
    sampled_logs = calculate_sampled_logs(logs, policy)
    reduction = (original_logs - sampled_logs) / original_logs

    print(f"   Original Logs: {original_logs:,}")
    print(f"   After Sampling: {sampled_logs:,}")
    print(f"   Reduction: {reduction:.1%}")
    print(f"   Cost Savings: ${calculate_cost_savings(original_logs, sampled_logs):.2f}/day")

    print(f"\n✨ Success! LipService reduces costs while maintaining observability!")
    print("=" * 70)


def generate_realistic_logs() -> list[LogEntry]:
    """Generate realistic log dataset for demo."""
    now = datetime.now()
    logs = []

    for i in range(500):
        logs.append(LogEntry(f"User {i % 100} logged in successfully", "INFO", now + timedelta(seconds=i), "web-api"))

    for i in range(300):
        logs.append(LogEntry(f"Cache hit for key session_{i % 50}", "DEBUG", now + timedelta(seconds=500 + i), "web-api"))

    for i in range(100):
        logs.append(LogEntry(f"API request /users/{i} completed in {i % 100}ms", "INFO", now + timedelta(seconds=800 + i), "web-api"))

    for i in range(20):
        logs.append(LogEntry("Database query slow (>1s)", "WARNING", now + timedelta(seconds=900 + i), "web-api"))

    for i in range(10):
        logs.append(LogEntry("Database connection timeout", "ERROR", now + timedelta(seconds=920 + i), "web-api"))

    logs.append(LogEntry("OutOfMemoryError: Java heap space", "CRITICAL", now + timedelta(seconds=930), "web-api"))

    return logs


def calculate_sampled_logs(logs: list[LogEntry], policy) -> int:
    """Calculate how many logs would be kept after sampling."""
    sampled = 0

    for log in logs:
        rate = policy.severity_rates.get(log.severity, 1.0)
        if rate >= 1.0 or (rate > 0 and hash(log.message) % 100 < rate * 100):
            sampled += 1

    return sampled


def calculate_cost_savings(original_logs: int, sampled_logs: int) -> float:
    """Calculate daily cost savings (assuming $0.10 per GB, ~1KB per log)."""
    gb_per_log = 0.001 / 1024
    original_cost = original_logs * gb_per_log * 0.10
    sampled_cost = sampled_logs * gb_per_log * 0.10
    return (original_cost - sampled_cost) * 24


if __name__ == "__main__":
    asyncio.run(main())

