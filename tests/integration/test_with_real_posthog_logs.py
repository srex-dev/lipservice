"""
Integration test: Python SDK with REAL PostHog logs

Fetches actual logs from PostHog and processes them through the SDK.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add SDK and backend to path
sdk_path = Path(__file__).parent.parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import structlog

from integrations.posthog_client import PostHogLogsClient
from lipservice import configure_adaptive_logging, get_logger, get_sampler, shutdown

logger = structlog.get_logger(__name__)


async def test_with_real_posthog_logs(
    clickhouse_host: str = "localhost:9000",
    team_id: int = 1,
    hours: int = 1,
):
    """Test SDK with real PostHog logs."""
    print("=" * 80)
    print("🎙️ LipService + PostHog: Real Log Integration Test")
    print("=" * 80)

    # Step 1: Fetch real logs from PostHog
    print("\n📥 Step 1: Fetch logs from PostHog")
    print("-" * 80)
    print(f"   ClickHouse: {clickhouse_host}")
    print(f"   Team ID: {team_id}")
    print(f"   Time range: Last {hours} hour(s)")
    
    try:
        client = PostHogLogsClient(clickhouse_host=clickhouse_host)
        logs = await client.fetch_logs(team_id, hours)
        
        if not logs:
            print("❌ No logs found in PostHog")
            print("\n💡 Tip: Make sure PostHog has logs for this team.")
            print("   You can generate logs by using PostHog or running a service.")
            return
        
        print(f"✅ Fetched {len(logs)} logs from PostHog")
        
        # Analyze log distribution
        severity_counts = {}
        service_counts = {}
        
        for log in logs:
            severity = log.severity
            service = log.service_name
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            service_counts[service] = service_counts.get(service, 0) + 1
        
        print(f"\n📊 Log Distribution:")
        print(f"   Severity breakdown:")
        for severity, count in sorted(severity_counts.items()):
            print(f"      {severity}: {count} logs ({count/len(logs)*100:.1f}%)")
        
        print(f"\n   Services found:")
        for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {service}: {count} logs")
        
    except Exception as e:
        print(f"❌ Failed to fetch logs: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Is PostHog running? (docker-compose up)")
        print("   - Is ClickHouse accessible?")
        print("   - Does the team have logs?")
        return

    # Step 2: Configure SDK
    print("\n🔧 Step 2: Configure LipService SDK")
    print("-" * 80)
    
    configure_adaptive_logging(
        service_name="posthog-integration-test",
        lipservice_url="http://localhost:8000",
        policy_refresh_interval=10,
        pattern_report_interval=20,
    )
    
    print("✅ SDK configured")
    
    # Wait for policy fetch
    await asyncio.sleep(2)
    
    sampler = get_sampler()
    if sampler and sampler.policy:
        print(f"✅ Policy loaded: v{sampler.policy.version}")
        print(f"   Global rate: {sampler.policy.global_rate}")
    else:
        print("⚠️  No policy yet (using fallback: 100%)")

    # Step 3: Process real logs through SDK
    print("\n🎯 Step 3: Process PostHog logs through SDK")
    print("-" * 80)
    
    sdk_logger = get_logger(__name__)
    sampled_count = 0
    dropped_count = 0
    severity_sampled = {}
    severity_dropped = {}
    
    for log in logs:
        message = log.message
        severity = log.severity.upper()
        
        # Log through SDK
        if severity == "DEBUG":
            sdk_logger.debug(message)
        elif severity == "INFO":
            sdk_logger.info(message)
        elif severity in ("WARN", "WARNING"):
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
                severity_sampled[severity] = severity_sampled.get(severity, 0) + 1
            else:
                dropped_count += 1
                severity_dropped[severity] = severity_dropped.get(severity, 0) + 1
    
    print(f"✅ Processed {len(logs)} logs")
    print(f"\n   Sampling results:")
    print(f"   - Sampled: {sampled_count} logs ({sampled_count/len(logs)*100:.1f}%)")
    print(f"   - Dropped: {dropped_count} logs ({dropped_count/len(logs)*100:.1f}%)")
    
    print(f"\n   Per-severity sampling:")
    all_severities = set(severity_sampled.keys()) | set(severity_dropped.keys())
    for sev in sorted(all_severities):
        sampled = severity_sampled.get(sev, 0)
        dropped = severity_dropped.get(sev, 0)
        total = sampled + dropped
        rate = (sampled / total * 100) if total > 0 else 0
        print(f"      {sev:10s}: {sampled:4d}/{total:4d} sampled ({rate:.1f}%)")

    # Step 4: Pattern analysis
    print("\n🔍 Step 4: Pattern Analysis")
    print("-" * 80)
    
    if sampler:
        stats = sampler.get_stats()
        print(f"✅ Patterns detected: {stats['patterns_tracked']}")
        
        if sampler.pattern_stats:
            print(f"\n   Top 10 patterns by frequency:")
            sorted_patterns = sorted(
                sampler.pattern_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            for i, (sig, data) in enumerate(sorted_patterns, 1):
                print(f"   {i:2d}. [{sig[:8]}] Count: {data['count']:4d}")
                print(f"       {data['message_sample'][:70]}...")

    # Step 5: Cost savings
    print("\n💰 Step 5: Cost Savings Projection")
    print("-" * 80)
    
    original_logs_per_hour = len(logs) / hours
    sampled_logs_per_hour = (sampled_count / len(logs)) * original_logs_per_hour
    
    # Cost calculation ($0.10/GB, 1KB/log)
    gb_per_log = 0.001 / 1024
    cost_per_gb = 0.10
    
    original_cost_daily = original_logs_per_hour * 24 * gb_per_log * cost_per_gb
    sampled_cost_daily = sampled_logs_per_hour * 24 * gb_per_log * cost_per_gb
    savings_daily = original_cost_daily - sampled_cost_daily
    
    original_cost_monthly = original_cost_daily * 30
    sampled_cost_monthly = sampled_cost_daily * 30
    savings_monthly = savings_daily * 30
    
    reduction_pct = ((original_cost_monthly - sampled_cost_monthly) / original_cost_monthly * 100) if original_cost_monthly > 0 else 0
    
    print(f"📊 Projected costs (based on {original_logs_per_hour:.0f} logs/hour):")
    print(f"\n   Without LipService:")
    print(f"   - Daily logs: {original_logs_per_hour * 24:,.0f}")
    print(f"   - Monthly cost: ${original_cost_monthly:.2f}")
    
    print(f"\n   With LipService:")
    print(f"   - Daily logs: {sampled_logs_per_hour * 24:,.0f}")
    print(f"   - Monthly cost: ${sampled_cost_monthly:.2f}")
    
    print(f"\n   💰 Savings:")
    print(f"   - Reduction: {reduction_pct:.1f}%")
    print(f"   - Monthly: ${savings_monthly:.2f}")
    print(f"   - Annual: ${savings_monthly * 12:.2f}")

    # Step 6: Verify error protection
    print("\n🛡️  Step 6: Error Protection Verification")
    print("-" * 80)
    
    error_logs = [log for log in logs if log.severity.upper() in ("ERROR", "CRITICAL")]
    if error_logs:
        error_sampled = severity_sampled.get("ERROR", 0) + severity_sampled.get("CRITICAL", 0)
        error_total = len(error_logs)
        error_retention = (error_sampled / error_total * 100) if error_total > 0 else 0
        
        print(f"   Total error/critical logs: {error_total}")
        print(f"   Errors sampled: {error_sampled}")
        print(f"   Retention rate: {error_retention:.0f}%")
        
        if error_retention >= 99:
            print(f"   ✅ Excellent! Virtually all errors captured!")
        elif error_retention >= 90:
            print(f"   ⚠️  Good, but some errors missed")
        else:
            print(f"   ❌ Warning: Significant error loss!")
    else:
        print(f"   ℹ️  No ERROR/CRITICAL logs in dataset")

    # Step 7: Cleanup
    print("\n🧹 Step 7: Cleanup")
    print("-" * 80)
    
    # Report patterns one more time
    if sampler:
        await sampler._report_patterns()
    
    await shutdown()
    print("✅ SDK shutdown complete")

    # Final summary
    print("\n" + "=" * 80)
    print("✨ REAL POSTHOG INTEGRATION TEST COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   ✅ Fetched {len(logs)} real logs from PostHog")
    print(f"   ✅ Detected {stats['patterns_tracked'] if sampler else 'N/A'} unique patterns")
    print(f"   ✅ Achieved {reduction_pct:.1f}% cost reduction")
    print(f"   ✅ Projected monthly savings: ${savings_monthly:.2f}")
    print(f"\n🎉 LipService is working with real PostHog data!")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LipService SDK with real PostHog logs")
    parser.add_argument("--clickhouse-host", default="localhost:9000", help="ClickHouse host:port")
    parser.add_argument("--team-id", type=int, default=1, help="PostHog team ID")
    parser.add_argument("--hours", type=int, default=1, help="Hours of logs to fetch")
    
    args = parser.parse_args()
    
    asyncio.run(test_with_real_posthog_logs(
        clickhouse_host=args.clickhouse_host,
        team_id=args.team_id,
        hours=args.hours,
    ))

