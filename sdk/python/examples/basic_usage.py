"""
Basic LipService SDK usage example.

Demonstrates the simplest way to integrate LipService into a Python application.
"""

import asyncio
import time

from lipservice import configure_adaptive_logging, get_logger, shutdown


async def main():
    """Run basic example."""
    print("🎙️ LipService SDK - Basic Usage Example")
    print("=" * 60)

    # Configure LipService (one line!)
    print("\n1. Configuring LipService...")
    configure_adaptive_logging(
        service_name="example-app",
        lipservice_url="http://localhost:8000",  # Your LipService API URL
    )
    print("   ✅ Configured!")

    # Get logger
    logger = get_logger(__name__)

    # Example 1: Normal info logs (will be sampled based on policy)
    print("\n2. Generating INFO logs...")
    for i in range(10):
        logger.info("user_action", user_id=f"user_{i}", action="page_view")
        time.sleep(0.1)
    print("   ✅ 10 INFO logs generated (intelligently sampled)")

    # Example 2: Debug logs (typically sampled at ~5%)
    print("\n3. Generating DEBUG logs...")
    for i in range(10):
        logger.debug("cache_hit", key=f"session_{i}")
        time.sleep(0.1)
    print("   ✅ 10 DEBUG logs generated (aggressively sampled)")

    # Example 3: Error logs (ALWAYS kept at 100%)
    print("\n4. Generating ERROR logs...")
    logger.error("payment_failed", user_id="user_123", amount=99.99, reason="card_declined")
    print("   ✅ ERROR log generated (100% sampling - never lost!)")

    # Example 4: Pattern variation
    print("\n5. Generating pattern variations...")
    for i in range(5):
        logger.info("api_request", endpoint=f"/users/{i}", method="GET", status=200)
    print("   ✅ Similar patterns detected and sampled together")

    # Wait a bit for background tasks
    print("\n6. Waiting for pattern reporting...")
    await asyncio.sleep(2)

    # Graceful shutdown
    print("\n7. Shutting down...")
    await shutdown()
    print("   ✅ Shutdown complete (final patterns reported)")

    print("\n" + "=" * 60)
    print("✨ Example complete!")
    print("\nKey Takeaways:")
    print("  • ERROR logs: 100% sampling (never lost)")
    print("  • INFO logs: ~20% sampling (cost reduction)")
    print("  • DEBUG logs: ~5% sampling (minimal noise)")
    print("  • Patterns detected automatically")
    print("  • Cost savings: ~70% reduction!")


if __name__ == "__main__":
    asyncio.run(main())

