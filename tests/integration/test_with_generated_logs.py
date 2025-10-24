"""
Test LipService with generated PostHog-style logs.

Uses realistic log patterns based on PostHog's codebase.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

import structlog

from lipservice import configure_adaptive_logging, get_logger, get_sampler, shutdown

logger = structlog.get_logger(__name__)


async def test_with_generated_logs(log_file: str = "posthog_test_logs.json"):
    """Test LipService with generated PostHog-style logs."""
    print("=" * 80)
    print("🎙️ LipService Test: Generated PostHog-Style Logs")
    print("=" * 80)

    # Step 1: Load generated logs
    print("\n📥 Step 1: Load Generated Logs")
    print("-" * 80)
    
    try:
        with open(log_file, "r") as f:
            logs = json.load(f)
        print(f"✅ Loaded {len(logs)} logs from {log_file}")
    except FileNotFoundError:
        print(f"❌ File not found: {log_file}")
        print("\n💡 Generate logs first:")
        print(f"   python tests/integration/generate_posthog_style_logs.py")
        return

    # Analyze distribution
    from collections import defaultdict
    severity_counts = defaultdict(int)
    for log in logs:
        severity_counts[log["severity_text"]] += 1
    
    print(f"\n📊 Log Distribution:")
    for severity, count in sorted(severity_counts.items()):
        pct = count / len(logs) * 100
        print(f"   {severity:10s}: {count:4d} logs ({pct:5.1f}%)")

    # Step 2: Configure SDK
    print("\n🔧 Step 2: Configure LipService SDK")
    print("-" * 80)
    
    configure_adaptive_logging(
        service_name="posthog-generated-test",
        lipservice_url="http://localhost:8000",
        policy_refresh_interval=10,
        pattern_report_interval=20,
    )
    
    print("✅ SDK configured")
    
    # Wait for policy
    await asyncio.sleep(2)
    
    sampler = get_sampler()
    if sampler and sampler.policy:
        print(f"✅ Policy loaded: v{sampler.policy.version}")
        print(f"   Global rate: {sampler.policy.global_rate}")
    else:
        print("⚠️  No policy yet (using fallback: 100%)")

    # Step 3: Process logs through SDK
    print("\n🎯 Step 3: Process Logs Through SDK")
    print("-" * 80)
    
    sdk_logger = get_logger(__name__)
    sampled_count = 0
    dropped_count = 0
    severity_sampled = defaultdict(int)
    severity_dropped = defaultdict(int)
    
    for log in logs:
        message = log["body"]
        severity = log["severity_text"]
        
        # Log through SDK
        if severity == "DEBUG":
            sdk_logger.debug(message)
        elif severity == "INFO":
            sdk_logger.info(message)
        elif severity == "WARNING":
            sdk_logger.warning(message)
        elif severity == "ERROR":
            sdk_logger.error(message)
        elif severity == "CRITICAL":
            sdk_logger.critical(message)
        
        # Track sampling
        if sampler:
            should_sample, _ = sampler.should_sample(message, severity)
            if should_sample:
                sampled_count += 1
                severity_sampled[severity] += 1
            else:
                dropped_count += 1
                severity_dropped[severity] += 1
    
    print(f"✅ Processed {len(logs)} logs")
    print(f"\n   Sampling Results:")
    print(f"   - Sampled: {sampled_count:5d} logs ({sampled_count/len(logs)*100:5.1f}%)")
    print(f"   - Dropped: {dropped_count:5d} logs ({dropped_count/len(logs)*100:5.1f}%)")
    
    print(f"\n   Per-Severity Sampling:")
    all_severities = set(severity_sampled.keys()) | set(severity_dropped.keys())
    for sev in sorted(all_severities):
        sampled = severity_sampled[sev]
        dropped = severity_dropped[sev]
        total = sampled + dropped
        rate = (sampled / total * 100) if total > 0 else 0
        print(f"      {sev:10s}: {sampled:4d}/{total:4d} sampled ({rate:5.1f}%)")

    # Step 4: Pattern analysis
    print("\n🔍 Step 4: Pattern Analysis")
    print("-" * 80)
    
    if sampler:
        stats = sampler.get_stats()
        print(f"✅ Patterns detected: {stats['patterns_tracked']}")
        
        if sampler.pattern_stats:
            print(f"\n   Top 10 Patterns:")
            sorted_patterns = sorted(
                sampler.pattern_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            for i, (sig, data) in enumerate(sorted_patterns, 1):
                print(f"   {i:2d}. [{sig[:8]}] {data['count']:4d} occurrences")
                print(f"       {data['message_sample'][:65]}...")

    # Step 5: Cost savings
    print("\n💰 Step 5: Cost Savings Projection")
    print("-" * 80)
    
    original_logs = len(logs)
    reduction_pct = (dropped_count / original_logs * 100) if original_logs > 0 else 0
    
    # Cost calculation
    gb_per_log = 0.001 / 1024
    cost_per_gb = 0.10
    
    original_cost_monthly = original_logs * 24 * 30 * gb_per_log * cost_per_gb
    sampled_cost_monthly = sampled_count * 24 * 30 * gb_per_log * cost_per_gb
    savings_monthly = original_cost_monthly - sampled_cost_monthly
    
    print(f"📊 Projected Costs (based on {original_logs} logs/hour):")
    print(f"\n   Without LipService:")
    print(f"   - Monthly logs: {original_logs * 24 * 30:,}")
    print(f"   - Monthly cost: ${original_cost_monthly:.2f}")
    
    print(f"\n   With LipService:")
    print(f"   - Monthly logs: {sampled_count * 24 * 30:,}")
    print(f"   - Monthly cost: ${sampled_cost_monthly:.2f}")
    
    print(f"\n   💰 Savings:")
    print(f"   - Reduction: {reduction_pct:.1f}%")
    print(f"   - Monthly: ${savings_monthly:.2f}")
    print(f"   - Annual: ${savings_monthly * 12:.2f}")

    # Step 6: Error protection
    print("\n🛡️  Step 6: Error Protection Verification")
    print("-" * 80)
    
    error_total = severity_counts.get("ERROR", 0) + severity_counts.get("CRITICAL", 0)
    error_sampled = severity_sampled.get("ERROR", 0) + severity_sampled.get("CRITICAL", 0)
    
    if error_total > 0:
        error_retention = (error_sampled / error_total * 100)
        print(f"   Total error/critical logs: {error_total}")
        print(f"   Errors sampled: {error_sampled}")
        print(f"   Retention rate: {error_retention:.0f}%")
        
        if error_retention >= 99:
            print(f"   ✅ Excellent! Virtually all errors captured!")
        else:
            print(f"   ⚠️  Some errors missed!")

    # Cleanup
    print("\n🧹 Step 7: Cleanup")
    print("-" * 80)
    
    await shutdown()
    print("✅ SDK shutdown complete")

    # Summary
    print("\n" + "=" * 80)
    print("✨ TEST COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   - Logs processed: {len(logs):,}")
    print(f"   - Patterns detected: {stats['patterns_tracked'] if sampler else 'N/A'}")
    print(f"   - Cost reduction: {reduction_pct:.1f}%")
    print(f"   - Monthly savings: ${savings_monthly:.2f}")
    print(f"   - Error retention: {error_retention:.0f}%" if error_total > 0 else "   - No errors in dataset")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test with generated PostHog-style logs")
    parser.add_argument("--file", default="posthog_test_logs.json", help="Log file to process")
    
    args = parser.parse_args()
    
    asyncio.run(test_with_generated_logs(args.file))

