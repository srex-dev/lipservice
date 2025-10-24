"""
High-volume performance testing for LipService.

This module provides:
- Load testing with high log volumes
- Performance benchmarking
- Memory usage monitoring
- Throughput measurement
- Stress testing
"""

import asyncio
import gc
import psutil
import time
from typing import Any, Dict, List

import pytest
import structlog

from lipservice import configure_adaptive_logging, get_logger, shutdown
from lipservice.performance import get_signature_cache, get_memory_pool, get_signature_computer


class LoadTester:
    """Load tester for LipService performance."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0
        self.start_time = 0
        self.measurements = []
    
    def start(self):
        """Start load testing."""
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
        gc.collect()  # Clean up before measurement
    
    def stop(self) -> Dict[str, Any]:
        """Stop load testing and return results."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        duration = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        
        result = {
            'duration_seconds': duration,
            'memory_delta_mb': memory_delta / (1024 * 1024),
            'peak_memory_mb': end_memory / (1024 * 1024),
            'cpu_percent': self.process.cpu_percent(),
        }
        
        self.measurements.append(result)
        return result


class TestHighVolumeLogging:
    """High-volume logging tests."""
    
    @pytest.mark.asyncio
    async def test_high_volume_logging(self):
        """Test high-volume logging performance."""
        configure_adaptive_logging(
            service_name='load-test',
            lipservice_url='http://localhost:8000',
            posthog_api_key='phc_test_key',
            posthog_team_id='12345',
            batch_size=1000,  # Large batch size
            flush_interval=1.0,  # Fast flush
        )

        logger = get_logger('load-test')
        load_tester = LoadTester()
        
        load_tester.start()
        
        # Generate high volume of logs
        num_logs = 10000
        for i in range(num_logs):
            logger.info(f"High volume log {i}", iteration=i, timestamp=time.time())
            
            # Log different patterns
            if i % 100 == 0:
                logger.error(f"Error log {i}", error_id=f"E{i}")
            elif i % 50 == 0:
                logger.warning(f"Warning log {i}", warning_id=f"W{i}")
        
        # Wait for processing
        await asyncio.sleep(5.0)
        
        result = load_tester.stop()
        
        # Calculate throughput
        throughput = num_logs / result['duration_seconds']
        
        # Performance assertions
        assert throughput > 1000  # At least 1000 logs/second
        assert result['memory_delta_mb'] < 100  # Memory usage should be reasonable
        assert result['duration_seconds'] < 30  # Should complete in reasonable time
        
        await shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_high_volume(self):
        """Test concurrent high-volume logging."""
        configure_adaptive_logging(
            service_name='concurrent-load-test',
            lipservice_url='http://localhost:8000',
            batch_size=500,
            flush_interval=0.5,
        )

        logger = get_logger('concurrent-load-test')
        load_tester = LoadTester()
        
        async def log_worker(worker_id: int, num_logs: int):
            """Worker function for concurrent logging."""
            for i in range(num_logs):
                logger.info(f"Worker {worker_id} log {i}", worker_id=worker_id, log_id=i)
                await asyncio.sleep(0.001)  # Small delay
        
        load_tester.start()
        
        # Start multiple concurrent workers
        tasks = []
        num_workers = 10
        logs_per_worker = 1000
        
        for worker_id in range(num_workers):
            task = asyncio.create_task(log_worker(worker_id, logs_per_worker))
            tasks.append(task)
        
        # Wait for all workers to complete
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(3.0)
        
        result = load_tester.stop()
        
        # Calculate total throughput
        total_logs = num_workers * logs_per_worker
        throughput = total_logs / result['duration_seconds']
        
        # Performance assertions
        assert throughput > 2000  # At least 2000 logs/second with concurrency
        assert result['memory_delta_mb'] < 150  # Memory usage should be reasonable
        
        await shutdown()

    @pytest.mark.asyncio
    async def test_memory_stress_test(self):
        """Test memory usage under stress."""
        configure_adaptive_logging(
            service_name='memory-stress-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('memory-stress-test')
        
        # Monitor memory usage
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        # Generate logs with large attributes
        for i in range(1000):
            large_data = "x" * 1000  # 1KB of data per log
            logger.info(f"Memory stress test {i}", data=large_data, iteration=i)
        
        # Wait for processing
        await asyncio.sleep(2.0)
        
        # Check memory usage
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 50  # Less than 50MB growth
        
        await shutdown()


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_signature_computation_benchmark(self):
        """Benchmark signature computation performance."""
        computer = get_signature_computer()
        
        # Test with various message sizes
        test_cases = [
            ("short", "User logged in"),
            ("medium", "User 123 logged in from IP 192.168.1.1 with session abc123"),
            ("long", "User 123 logged in from IP 192.168.1.1 with session abc123 and additional context " * 10),
        ]
        
        for case_name, message in test_cases:
            start_time = time.time()
            
            # Compute signatures
            for _ in range(1000):
                computer.compute_signature(message)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should be fast regardless of message size
            assert duration < 1.0, f"Signature computation too slow for {case_name} message"
    
    def test_cache_performance_benchmark(self):
        """Benchmark cache performance."""
        cache = get_signature_cache()
        
        # Pre-populate cache
        test_messages = [f"Test message {i}" for i in range(1000)]
        for message in test_messages:
            cache.put(message, f"signature_{hash(message)}")
        
        # Benchmark cache hits
        start_time = time.time()
        
        for _ in range(10000):
            for message in test_messages:
                cache.get(message)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast
        assert duration < 0.5
        
        # Check hit rate
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0.95
    
    def test_memory_pool_benchmark(self):
        """Benchmark memory pool performance."""
        pool = get_memory_pool()
        
        start_time = time.time()
        
        # Allocate and return blocks
        blocks = []
        for _ in range(1000):
            block = pool.get_block()
            blocks.append(block)
        
        # Return blocks
        for block in blocks:
            pool.return_block(block)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast
        assert duration < 0.1
        
        # Check pool stats
        stats = pool.get_stats()
        assert stats['total_allocated'] <= 100


class TestStressTesting:
    """Stress testing scenarios."""
    
    @pytest.mark.asyncio
    async def test_rapid_configuration_changes(self):
        """Test rapid configuration changes."""
        # Rapidly configure and reconfigure
        for i in range(10):
            configure_adaptive_logging(
                service_name=f'stress-test-{i}',
                lipservice_url='http://localhost:8000',
                policy_refresh_interval=1,
                pattern_report_interval=1,
            )
            
            logger = get_logger(f'stress-test-{i}')
            logger.info(f"Stress test configuration {i}", config_id=i)
            
            await asyncio.sleep(0.1)
        
        # Should not crash
        assert True
        
        await shutdown()

    @pytest.mark.asyncio
    async def test_mixed_log_levels_stress(self):
        """Test stress with mixed log levels."""
        configure_adaptive_logging(
            service_name='mixed-levels-stress',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('mixed-levels-stress')
        
        # Generate logs with mixed levels
        for i in range(5000):
            level = ["INFO", "WARNING", "ERROR", "DEBUG"][i % 4]
            logger.log(level, f"Mixed level log {i}", level=level, iteration=i)
        
        # Wait for processing
        await asyncio.sleep(2.0)
        
        # Should not crash
        assert True
        
        await shutdown()

    @pytest.mark.asyncio
    async def test_large_attribute_stress(self):
        """Test stress with large attributes."""
        configure_adaptive_logging(
            service_name='large-attributes-stress',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('large-attributes-stress')
        
        # Generate logs with large attributes
        for i in range(1000):
            large_attr = {"data": "x" * 10000}  # 10KB attribute
            logger.info(f"Large attribute log {i}", **large_attr, iteration=i)
        
        # Wait for processing
        await asyncio.sleep(2.0)
        
        # Should not crash
        assert True
        
        await shutdown()


class TestResourceMonitoring:
    """Resource monitoring tests."""
    
    def test_cpu_usage_monitoring(self):
        """Monitor CPU usage during operations."""
        process = psutil.Process()
        
        # Monitor CPU during signature computation
        cpu_before = process.cpu_percent()
        
        computer = get_signature_computer()
        for i in range(10000):
            computer.compute_signature(f"CPU test message {i}")
        
        cpu_after = process.cpu_percent()
        
        # CPU usage should be reasonable
        assert cpu_after < 50  # Less than 50% CPU usage
    
    def test_memory_leak_detection(self):
        """Detect memory leaks."""
        process = psutil.Process()
        
        # Get initial memory
        initial_memory = process.memory_info().rss
        
        # Perform operations
        cache = get_signature_cache()
        pool = get_memory_pool()
        
        for cycle in range(10):
            # Add to cache
            for i in range(1000):
                message = f"Memory test message {cycle}_{i}"
                cache.put(message, f"signature_{hash(message)}")
            
            # Use memory pool
            blocks = []
            for _ in range(100):
                block = pool.get_block()
                blocks.append(block)
            
            for block in blocks:
                pool.return_block(block)
            
            # Force garbage collection
            gc.collect()
            
            # Check memory
            current_memory = process.memory_info().rss
            memory_growth = (current_memory - initial_memory) / (1024 * 1024)
            
            # Memory growth should be reasonable
            assert memory_growth < 100  # Less than 100MB growth


if __name__ == "__main__":
    # Run load tests
    pytest.main([__file__, "-v", "--tb=short"])
