"""
PostHog integration example for LipService SDK.

This example demonstrates how to use LipService with PostHog's logging
infrastructure for intelligent log sampling and cost reduction.
"""

import asyncio
import logging
import time
from datetime import datetime

import structlog

from lipservice import configure_adaptive_logging, get_logger


def basic_posthog_integration():
    """Basic PostHog integration with one-line configuration."""
    print("=== Basic PostHog Integration ===")
    
    # One-line configuration with PostHog
    configure_adaptive_logging(
        service_name="my-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",  # Your PostHog API key
        posthog_team_id="12345",    # Your PostHog team ID
    )
    
    # Get logger and start logging
    logger = get_logger(__name__)
    
    # These logs will be intelligently sampled and sent to PostHog
    logger.info("user_login", user_id=123, action="login")
    logger.info("user_login", user_id=456, action="login")  # Same pattern, sampled together
    logger.warning("rate_limit_exceeded", user_id=123, limit=100)
    logger.error("payment_failed", user_id=123, amount=99.99)  # Always kept!
    logger.debug("cache_hit", key="user:123")  # Sampled at low rate
    
    print("✅ Logs sent to PostHog with intelligent sampling!")


def advanced_posthog_integration():
    """Advanced PostHog integration with custom configuration."""
    print("\n=== Advanced PostHog Integration ===")
    
    # Advanced configuration
    configure_adaptive_logging(
        service_name="ecommerce-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="12345",
        posthog_endpoint="https://app.posthog.com",  # PostHog Cloud
        policy_refresh_interval=300,  # Refresh policies every 5 minutes
        pattern_report_interval=600,  # Report patterns every 10 minutes
        use_structlog=True,  # Use structured logging
    )
    
    # Get structured logger
    logger = get_logger(__name__)
    
    # Simulate different types of logs
    log_scenarios = [
        # High-frequency INFO logs (will be heavily sampled)
        ("user_action", {"user_id": 123, "action": "page_view", "page": "/products"}),
        ("user_action", {"user_id": 124, "action": "page_view", "page": "/products"}),
        ("user_action", {"user_id": 125, "action": "page_view", "page": "/products"}),
        
        # WARNING logs (moderate sampling)
        ("rate_limit_warning", {"user_id": 123, "limit": 100, "current": 95}),
        ("slow_query", {"query": "SELECT * FROM users", "duration": 2.5}),
        
        # ERROR logs (always kept at 100%)
        ("payment_error", {"user_id": 123, "error": "insufficient_funds", "amount": 99.99}),
        ("database_error", {"error": "connection_timeout", "retry_count": 3}),
        
        # DEBUG logs (minimal sampling)
        ("cache_debug", {"key": "user:123", "hit": True}),
        ("performance_debug", {"function": "process_order", "duration": 0.1}),
    ]
    
    # Log all scenarios
    for event, context in log_scenarios:
        logger.info(event, **context)
        time.sleep(0.1)  # Small delay between logs
    
    print("✅ Advanced logging with PostHog integration complete!")


def self_hosted_posthog_integration():
    """Integration with self-hosted PostHog instance."""
    print("\n=== Self-Hosted PostHog Integration ===")
    
    # Configuration for self-hosted PostHog
    configure_adaptive_logging(
        service_name="internal-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="67890",
        posthog_endpoint="https://posthog.company.com",  # Self-hosted endpoint
    )
    
    logger = get_logger(__name__)
    
    # Log to self-hosted PostHog
    logger.info("deployment_started", version="1.2.3", environment="production")
    logger.info("health_check", service="api", status="healthy")
    logger.warning("high_memory_usage", service="api", usage_percent=85)
    logger.error("service_unavailable", service="database", error="connection_failed")
    
    print("✅ Logs sent to self-hosted PostHog!")


def cost_savings_demonstration():
    """Demonstrate cost savings with PostHog integration."""
    print("\n=== Cost Savings Demonstration ===")
    
    configure_adaptive_logging(
        service_name="high-volume-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="12345",
    )
    
    logger = get_logger(__name__)
    
    # Simulate high-volume logging
    print("Simulating high-volume logging...")
    
    # Generate 1000 logs with different patterns
    for i in range(1000):
        if i % 10 == 0:
            # ERROR logs (always kept)
            logger.error("critical_error", error_id=i, message="Something went wrong")
        elif i % 5 == 0:
            # WARNING logs (moderate sampling)
            logger.warning("performance_warning", request_id=i, duration=2.5)
        else:
            # INFO logs (heavy sampling)
            logger.info("request_processed", request_id=i, user_id=i % 100)
    
    print("✅ Generated 1000 logs with intelligent sampling!")
    print("📊 Expected cost reduction: 50-80%")
    print("🛡️ All ERROR logs preserved (100%)")


def framework_integration_examples():
    """Examples for different Python frameworks."""
    print("\n=== Framework Integration Examples ===")
    
    # FastAPI example
    print("FastAPI Integration:")
    print("""
    from fastapi import FastAPI
    from lipservice import configure_adaptive_logging
    
    app = FastAPI()
    
    # Configure LipService with PostHog
    configure_adaptive_logging(
        service_name="fastapi-app",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="12345",
    )
    
    @app.get("/")
    async def root():
        logger = get_logger(__name__)
        logger.info("endpoint_hit", endpoint="/", method="GET")
        return {"message": "Hello World"}
    """)
    
    # Django example
    print("\nDjango Integration:")
    print("""
    # settings.py
    LIPSERVICE = {
        'SERVICE_NAME': 'django-app',
        'LIPSERVICE_URL': 'https://lipservice.company.com',
        'POSTHOG_API_KEY': 'phc_xxx',
        'POSTHOG_TEAM_ID': '12345',
    }
    
    # In your Django app
    from lipservice import configure_adaptive_logging, get_logger
    
    configure_adaptive_logging(**LIPSERVICE)
    logger = get_logger(__name__)
    
    def my_view(request):
        logger.info("view_accessed", view="my_view", user=request.user.id)
        return HttpResponse("Hello World")
    """)
    
    # Flask example
    print("\nFlask Integration:")
    print("""
    from flask import Flask
    from lipservice import configure_adaptive_logging, get_logger
    
    app = Flask(__name__)
    
    # Configure LipService with PostHog
    configure_adaptive_logging(
        service_name="flask-app",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="12345",
    )
    
    @app.route('/')
    def hello():
        logger = get_logger(__name__)
        logger.info("route_hit", route="/", method="GET")
        return 'Hello World!'
    """)


async def async_logging_example():
    """Example of async logging with PostHog."""
    print("\n=== Async Logging Example ===")
    
    configure_adaptive_logging(
        service_name="async-api",
        lipservice_url="https://lipservice.company.com",
        posthog_api_key="phc_xxx",
        posthog_team_id="12345",
    )
    
    logger = get_logger(__name__)
    
    # Simulate async operations
    async def process_user(user_id: int):
        logger.info("user_processing_started", user_id=user_id)
        await asyncio.sleep(0.1)  # Simulate work
        logger.info("user_processing_completed", user_id=user_id)
    
    # Process multiple users concurrently
    tasks = [process_user(i) for i in range(10)]
    await asyncio.gather(*tasks)
    
    print("✅ Async logging with PostHog complete!")


def main():
    """Run all PostHog integration examples."""
    print("🎙️ LipService + PostHog Integration Examples")
    print("=" * 50)
    
    # Run synchronous examples
    basic_posthog_integration()
    advanced_posthog_integration()
    self_hosted_posthog_integration()
    cost_savings_demonstration()
    framework_integration_examples()
    
    # Run async example
    asyncio.run(async_logging_example())
    
    print("\n🎉 All PostHog integration examples completed!")
    print("\nKey Benefits:")
    print("✅ 50-80% cost reduction on log storage")
    print("✅ Zero data loss (ERROR logs always kept)")
    print("✅ One-line PostHog integration")
    print("✅ Intelligent pattern-based sampling")
    print("✅ Real-time policy updates")
    print("✅ Works with PostHog Cloud and self-hosted")


if __name__ == "__main__":
    main()
