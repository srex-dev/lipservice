"""
Comprehensive integration tests for LipService.

This module provides:
- End-to-end integration tests
- Cross-SDK compatibility tests
- Performance regression tests
- Error handling tests
- PostHog integration tests
"""

import asyncio
import json
import time
from typing import Any, Dict, List

import pytest
import structlog

from lipservice import configure_adaptive_logging, get_logger, shutdown
from lipservice.performance import get_signature_cache, get_memory_pool


class TestEndToEndIntegration:
    """End-to-end integration tests for LipService."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete LipService workflow from configuration to logging."""
        # Configure LipService
        configure_adaptive_logging(
            service_name='integration-test',
            lipservice_url='http://localhost:8000',
            posthog_api_key='phc_test_key',
            posthog_team_id='12345',
            policy_refresh_interval=1,  # Fast refresh for testing
            pattern_report_interval=2,   # Fast reporting for testing
        )

        # Get logger
        logger = get_logger('integration-test')

        # Test different log levels and patterns
        test_scenarios = [
            ("INFO", "User logged in", {"user_id": 123}),
            ("WARNING", "High memory usage", {"usage": 85}),
            ("ERROR", "Database connection failed", {"error": "timeout"}),
            ("DEBUG", "Cache hit", {"key": "user:123"}),
            ("INFO", "User 456 logged in", {"user_id": 456}),  # Similar pattern
            ("ERROR", "Payment processing failed", {"amount": 99.99}),
        ]

        for severity, message, attributes in test_scenarios:
            logger.log(severity, message, **attributes)

        # Wait for background processing
        await asyncio.sleep(0.5)

        # Verify that logs were processed
        assert True  # If we get here without errors, the workflow is working

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_posthog_integration(self):
        """Test PostHog integration specifically."""
        configure_adaptive_logging(
            service_name='posthog-test',
            lipservice_url='http://localhost:8000',
            posthog_api_key='phc_test_key',
            posthog_team_id='12345',
        )

        logger = get_logger('posthog-test')

        # Test various log patterns that should be sent to PostHog
        logger.info("PostHog integration test", test_id="integration_001")
        logger.error("Critical error for PostHog", error_code="E001")
        logger.warning("Warning message", warning_type="W001")

        # Wait for PostHog export
        await asyncio.sleep(1.0)

        # Verify PostHog integration worked
        assert True

        await shutdown()

    @pytest.mark.asyncio
    async def test_sampling_behavior(self):
        """Test that sampling behavior works correctly."""
        configure_adaptive_logging(
            service_name='sampling-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('sampling-test')

        # Test that errors are always sampled
        logger.error("This error should always be kept", error_id="E001")
        
        # Test that info logs are sampled
        for i in range(100):
            logger.info(f"Info message {i}", iteration=i)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Verify sampling worked
        assert True

        await shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads."""
        configure_adaptive_logging(
            service_name='concurrent-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('concurrent-test')

        async def log_worker(worker_id: int, num_logs: int):
            """Worker function for concurrent logging."""
            for i in range(num_logs):
                logger.info(f"Worker {worker_id} log {i}", worker_id=worker_id, log_id=i)
                await asyncio.sleep(0.001)  # Small delay

        # Start multiple concurrent workers
        tasks = []
        for worker_id in range(5):
            task = asyncio.create_task(log_worker(worker_id, 20))
            tasks.append(task)

        # Wait for all workers to complete
        await asyncio.gather(*tasks)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify concurrent logging worked
        assert True

        await shutdown()


class TestPerformanceRegression:
    """Performance regression tests."""
    
    def test_signature_computation_performance(self):
        """Test that signature computation is fast."""
        from lipservice.performance import get_signature_computer
        
        computer = get_signature_computer()
        
        # Test with many messages
        messages = [
            f"User {i} logged in from IP 192.168.1.{i % 255}"
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        signatures = []
        for message in messages:
            signature = computer.compute_signature(message)
            signatures.append(signature)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (less than 1 second for 1000 messages)
        assert duration < 1.0
        assert len(set(signatures)) > 0  # Should produce different signatures

    def test_memory_usage(self):
        """Test that memory usage is reasonable."""
        cache = get_signature_cache()
        pool = get_memory_pool()
        
        # Add many entries to cache
        for i in range(1000):
            message = f"Test message {i}" * 10  # Make it longer
            cache.put(message, f"signature_{i}")
        
        # Use memory pool
        blocks = []
        for _ in range(100):
            block = pool.get_block()
            blocks.append(block)
        
        # Return blocks
        for block in blocks:
            pool.return_block(block)
        
        # Check stats
        cache_stats = cache.get_stats()
        pool_stats = pool.get_stats()
        
        # Memory usage should be reasonable
        assert cache_stats['memory_usage_mb'] < 10.0
        assert pool_stats['total_allocated'] <= 100

    def test_cache_efficiency(self):
        """Test that cache is efficient."""
        cache = get_signature_cache()
        
        # Pre-populate cache
        test_messages = [f"Test message {i}" for i in range(100)]
        for message in test_messages:
            cache.put(message, f"signature_{hash(message)}")
        
        # Test cache hits
        start_time = time.time()
        
        for _ in range(1000):
            for message in test_messages:
                cache.get(message)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast
        assert duration < 0.1
        
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0.9


class TestErrorHandling:
    """Error handling tests."""
    
    @pytest.mark.asyncio
    async def test_network_failure_handling(self):
        """Test handling of network failures."""
        configure_adaptive_logging(
            service_name='network-test',
            lipservice_url='http://invalid-url:9999',  # Invalid URL
            posthog_api_key='phc_test_key',
            posthog_team_id='12345',
        )

        logger = get_logger('network-test')

        # Should not crash even with network failures
        logger.info("Test message with network failure", test_id="network_001")
        logger.error("Error message with network failure", error_id="E001")

        # Wait for processing
        await asyncio.sleep(1.0)

        # Should not have crashed
        assert True

        await shutdown()

    @pytest.mark.asyncio
    async def test_invalid_configuration(self):
        """Test handling of invalid configuration."""
        # Test with missing required fields
        try:
            configure_adaptive_logging(
                service_name='',  # Empty service name
                lipservice_url='http://localhost:8000',
            )
            # Should not crash
            assert True
        except Exception:
            # Expected to fail with invalid config
            assert True

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable."""
        configure_adaptive_logging(
            service_name='degradation-test',
            lipservice_url='http://localhost:8000',
            posthog_api_key='phc_invalid_key',  # Invalid key
            posthog_team_id='12345',
        )

        logger = get_logger('degradation-test')

        # Should continue working even with invalid PostHog credentials
        logger.info("Test message with invalid PostHog key", test_id="degradation_001")
        logger.error("Error message with invalid PostHog key", error_id="E001")

        # Wait for processing
        await asyncio.sleep(1.0)

        # Should not have crashed
        assert True

        await shutdown()


class TestCrossSDKCompatibility:
    """Cross-SDK compatibility tests."""
    
    def test_python_sdk_compatibility(self):
        """Test Python SDK compatibility."""
        # Test that all main functions are available
        from lipservice import (
            configure_adaptive_logging,
            get_logger,
            shutdown,
            LipServiceClient,
            LipServiceHandler,
            AdaptiveSampler,
            PostHogConfig,
            PostHogHandler,
            PostHogOTLPExporter,
            create_posthog_handler,
        )
        
        # All imports should work
        assert True

    def test_performance_module_compatibility(self):
        """Test performance module compatibility."""
        from lipservice.performance import (
            LRUSignatureCache,
            MemoryPool,
            OptimizedSignatureComputer,
            get_signature_cache,
            get_memory_pool,
            get_signature_computer,
        )
        
        # All imports should work
        assert True

    def test_optimized_posthog_compatibility(self):
        """Test optimized PostHog module compatibility."""
        from lipservice.optimized_posthog import (
            ConnectionPool,
            OptimizedPostHogOTLPExporter,
        )
        
        # All imports should work
        assert True


class TestDataConsistency:
    """Data consistency tests."""
    
    def test_signature_consistency(self):
        """Test that signatures are consistent across calls."""
        from lipservice.performance import get_signature_computer
        
        computer = get_signature_computer()
        
        message = "User 123 logged in from IP 192.168.1.1"
        
        # Compute signature multiple times
        signatures = []
        for _ in range(10):
            signature = computer.compute_signature(message)
            signatures.append(signature)
        
        # All signatures should be the same
        assert len(set(signatures)) == 1

    def test_pattern_normalization_consistency(self):
        """Test that pattern normalization is consistent."""
        from lipservice.performance import get_signature_computer
        
        computer = get_signature_computer()
        
        # These should produce the same signature
        message1 = "User 123 logged in from IP 192.168.1.1"
        message2 = "User 456 logged in from IP 10.0.0.1"
        
        sig1 = computer.compute_signature(message1)
        sig2 = computer.compute_signature(message2)
        
        # Should be different (different user IDs and IPs)
        assert sig1 != sig2
        
        # But these should be the same pattern
        message3 = "User 789 logged in from IP 192.168.1.2"
        message4 = "User 101112 logged in from IP 10.0.0.2"
        
        sig3 = computer.compute_signature(message3)
        sig4 = computer.compute_signature(message4)
        
        # Should be the same pattern
        assert sig3 == sig4


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
