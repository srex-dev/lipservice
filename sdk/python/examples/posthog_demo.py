"""
Simple PostHog integration demo for LipService SDK.

This demonstrates the one-line PostHog integration with intelligent sampling.
"""

import asyncio
import logging
import time
from datetime import datetime

from lipservice import configure_adaptive_logging, get_logger


def demo_posthog_integration():
    """Demonstrate PostHog integration with LipService."""
    print("🎙️ LipService + PostHog Integration Demo")
    print("=" * 50)
    
    # One-line PostHog integration
    configure_adaptive_logging(
        service_name="demo-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_demo_key",  # Replace with your PostHog API key
        posthog_team_id="12345",         # Replace with your PostHog team ID
    )
    
    # Get logger
    logger = get_logger(__name__)
    
    print("✅ LipService configured with PostHog integration!")
    print("📊 Logs will be intelligently sampled and sent to PostHog")
    print()
    
    # Simulate different types of logs
    print("Generating sample logs...")
    
    # High-frequency INFO logs (will be heavily sampled)
    for i in range(10):
        logger.info("user_action", user_id=i, action="page_view", page="/products")
        time.sleep(0.1)
    
    # WARNING logs (moderate sampling)
    logger.warning("rate_limit_warning", user_id=123, limit=100, current=95)
    logger.warning("slow_query", query="SELECT * FROM users", duration=2.5)
    
    # ERROR logs (always kept at 100%)
    logger.error("payment_error", user_id=123, error="insufficient_funds", amount=99.99)
    logger.error("database_error", error="connection_timeout", retry_count=3)
    
    # DEBUG logs (minimal sampling)
    logger.debug("cache_hit", key="user:123", hit=True)
    logger.debug("performance_debug", function="process_order", duration=0.1)
    
    print("✅ Sample logs generated!")
    print()
    print("📈 Expected Results:")
    print("- INFO logs: ~20% sampled (2 out of 10)")
    print("- WARNING logs: ~50% sampled (1 out of 2)")
    print("- ERROR logs: 100% sampled (2 out of 2)")
    print("- DEBUG logs: ~5% sampled (0-1 out of 2)")
    print()
    print("💰 Cost Savings: ~70% reduction in log volume!")
    print("🛡️ Zero data loss: All ERROR logs preserved")


def demo_without_posthog():
    """Demonstrate LipService without PostHog (basic mode)."""
    print("\n" + "=" * 50)
    print("🎙️ LipService Basic Mode (No PostHog)")
    print("=" * 50)
    
    # Basic configuration without PostHog
    configure_adaptive_logging(
        service_name="basic-api",
        lipservice_url="https://lipservice.company.com",
        use_structlog=True,
    )
    
    logger = get_logger(__name__)
    
    print("✅ LipService configured in basic mode!")
    print("📊 Logs will be intelligently sampled (no PostHog export)")
    print()
    
    # Generate some logs
    logger.info("service_started", version="1.0.0")
    logger.info("user_login", user_id=456)
    logger.warning("memory_usage_high", usage_percent=85)
    logger.error("critical_error", message="Service unavailable")
    
    print("✅ Basic mode logs generated!")
    print("📝 Logs are sampled but not exported to PostHog")


def demo_cost_calculation():
    """Demonstrate cost savings calculation."""
    print("\n" + "=" * 50)
    print("💰 Cost Savings Calculator")
    print("=" * 50)
    
    # Simulate high-volume logging
    print("Simulating high-volume application...")
    
    configure_adaptive_logging(
        service_name="high-volume-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_demo_key",
        posthog_team_id="12345",
    )
    
    logger = get_logger(__name__)
    
    # Generate 100 logs with typical distribution
    total_logs = 100
    debug_logs = 40  # 40%
    info_logs = 40   # 40%
    warning_logs = 15 # 15%
    error_logs = 5   # 5%
    
    print(f"Generating {total_logs} logs with typical distribution...")
    
    # DEBUG logs (5% sampling)
    for i in range(debug_logs):
        logger.debug("debug_message", request_id=i, data="debug_data")
    
    # INFO logs (20% sampling)
    for i in range(info_logs):
        logger.info("user_action", user_id=i, action="click", element="button")
    
    # WARNING logs (50% sampling)
    for i in range(warning_logs):
        logger.warning("performance_warning", request_id=i, duration=1.5)
    
    # ERROR logs (100% sampling)
    for i in range(error_logs):
        logger.error("critical_error", request_id=i, error="timeout")
    
    print("✅ High-volume logging simulation complete!")
    print()
    
    # Calculate expected savings
    expected_sampled = (debug_logs * 0.05) + (info_logs * 0.20) + (warning_logs * 0.50) + (error_logs * 1.0)
    savings_percent = ((total_logs - expected_sampled) / total_logs) * 100
    
    print("📊 Expected Results:")
    print(f"- Total logs generated: {total_logs}")
    print(f"- Expected logs sent to PostHog: ~{expected_sampled:.0f}")
    print(f"- Cost reduction: ~{savings_percent:.1f}%")
    print()
    print("💡 At scale (1M logs/day):")
    print(f"- Without LipService: $500/month")
    print(f"- With LipService: ~${500 * (expected_sampled/total_logs):.0f}/month")
    print(f"- Monthly savings: ~${500 - (500 * (expected_sampled/total_logs)):.0f}")


def main():
    """Run all PostHog integration demos."""
    try:
        # Demo 1: PostHog integration
        demo_posthog_integration()
        
        # Demo 2: Basic mode
        demo_without_posthog()
        
        # Demo 3: Cost calculation
        demo_cost_calculation()
        
        print("\n" + "=" * 50)
        print("🎉 All demos completed successfully!")
        print("=" * 50)
        print()
        print("🚀 Next Steps:")
        print("1. Replace 'phc_demo_key' with your actual PostHog API key")
        print("2. Replace '12345' with your actual PostHog team ID")
        print("3. Deploy to your application")
        print("4. Monitor cost savings in PostHog!")
        print()
        print("📚 Documentation: https://github.com/srex-dev/lipservice")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure you have the required dependencies installed:")
        print("   pip install lipservice-sdk")


if __name__ == "__main__":
    main()
