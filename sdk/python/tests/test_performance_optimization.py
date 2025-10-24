"""
Performance tests for LipService optimizations.

This module provides:
- Memory usage profiling
- Throughput testing
- Latency measurement
- Performance benchmarking
"""

import asyncio
import gc
import psutil
import time
from typing import Any, Dict, List

import pytest
import structlog

from lipservice.performance import (
    LRUSignatureCache,
    MemoryPool,
    OptimizedSignatureComputer,
    get_memory_pool,
    get_signature_cache,
    get_signature_computer,
)
from lipservice.optimized_posthog import OptimizedPostHogOTLPExporter

logger = structlog.get_logger(__name__)


class PerformanceProfiler:
    """Performance profiler for LipService components."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0
        self.start_time = 0
        self.measurements = []
    
    def start(self):
        """Start profiling."""
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
        gc.collect()  # Clean up before measurement
    
    def stop(self) -> Dict[str, Any]:
        """Stop profiling and return results."""
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


class TestSignatureCachePerformance:
    """Test signature cache performance."""
    
    def test_cache_hit_performance(self):
        """Test cache hit performance."""
        cache = LRUSignatureCache(max_size=1000)
        
        # Pre-populate cache
        test_messages = [f"Test message {i}" for i in range(100)]
        for message in test_messages:
            cache.put(message, f"signature_{hash(message)}")
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        # Test cache hits
        for _ in range(1000):
            for message in test_messages:
                cache.get(message)
        
        result = profiler.stop()
        
        # Should be very fast
        assert result['duration_seconds'] < 0.1
        assert result['memory_delta_mb'] < 1.0
        
        stats = cache.get_stats()
        assert stats['hit_rate'] > 0.9
    
    def test_cache_memory_usage(self):
        """Test cache memory usage limits."""
        cache = LRUSignatureCache(max_size=100, max_memory_mb=1)
        
        # Add many entries
        for i in range(1000):
            message = f"Very long message with lots of content {i}" * 10
            cache.put(message, f"signature_{i}")
        
        stats = cache.get_stats()
        
        # Should respect limits
        assert stats['size'] <= 100
        assert stats['memory_usage_mb'] <= 1.0


class TestSignatureComputerPerformance:
    """Test signature computer performance."""
    
    def test_signature_computation_speed(self):
        """Test signature computation speed."""
        computer = OptimizedSignatureComputer(cache_size=1000)
        
        test_messages = [
            "User 123 logged in from IP 192.168.1.1",
            "Database query executed in 45ms",
            "Error occurred: Connection timeout after 30s",
            "Cache hit for key user:456",
            "Request processed successfully",
        ] * 100  # 500 messages total
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        signatures = []
        for message in test_messages:
            signature = computer.compute_signature(message)
            signatures.append(signature)
        
        result = profiler.stop()
        
        # Should be fast
        assert result['duration_seconds'] < 1.0
        assert len(set(signatures)) > 0  # Should produce different signatures
        
        stats = computer.get_stats()
        assert stats['cache_stats']['hit_rate'] > 0.5  # Should have cache hits
    
    def test_signature_normalization(self):
        """Test signature normalization consistency."""
        computer = OptimizedSignatureComputer()
        
        # These should produce the same signature
        message1 = "User 123 logged in from IP 192.168.1.1"
        message2 = "User 456 logged in from IP 10.0.0.1"
        
        sig1 = computer.compute_signature(message1)
        sig2 = computer.compute_signature(message2)
        
        # Should be different (different user IDs and IPs)
        assert sig1 != sig2
        
        # But these should be the same
        message3 = "User 789 logged in from IP 192.168.1.2"
        message4 = "User 101112 logged in from IP 10.0.0.2"
        
        sig3 = computer.compute_signature(message3)
        sig4 = computer.compute_signature(message4)
        
        # Should be the same pattern
        assert sig3 == sig4


class TestMemoryPoolPerformance:
    """Test memory pool performance."""
    
    def test_memory_pool_efficiency(self):
        """Test memory pool efficiency."""
        pool = MemoryPool(block_size=1024, max_blocks=10)
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        # Allocate and return blocks
        blocks = []
        for _ in range(100):
            block = pool.get_block()
            blocks.append(block)
        
        # Return blocks
        for block in blocks:
            pool.return_block(block)
        
        result = profiler.stop()
        
        # Should be efficient
        assert result['duration_seconds'] < 0.1
        assert result['memory_delta_mb'] < 1.0
        
        stats = pool.get_stats()
        assert stats['available_blocks'] <= 10
        assert stats['total_allocated'] <= 10


class TestPostHogExporterPerformance:
    """Test PostHog exporter performance."""
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """Test batch processing performance."""
        exporter = OptimizedPostHogOTLPExporter(
            api_key="phc_test",
            team_id="12345",
            batch_size=50,
            flush_interval=0.1,
        )
        
        await exporter.start()
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        # Export many logs
        for i in range(500):
            await exporter.export_log(
                message=f"Test message {i}",
                severity="INFO",
                timestamp=time.time(),
                user_id=i,
            )
        
        # Wait for processing
        await asyncio.sleep(1.0)
        
        result = profiler.stop()
        
        # Should be efficient
        assert result['duration_seconds'] < 2.0
        assert result['memory_delta_mb'] < 10.0
        
        stats = exporter.get_stats()
        assert stats['logs_exported'] > 0
        assert stats['batches_sent'] > 0
        
        await exporter.stop()
    
    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Test high throughput performance."""
        exporter = OptimizedPostHogOTLPExporter(
            api_key="phc_test",
            team_id="12345",
            batch_size=100,
            flush_interval=0.05,
        )
        
        await exporter.start()
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        # High throughput test
        tasks = []
        for i in range(1000):
            task = exporter.export_log(
                message=f"High throughput message {i}",
                severity="INFO",
                timestamp=time.time(),
                iteration=i,
            )
            tasks.append(task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(2.0)
        
        result = profiler.stop()
        
        # Calculate throughput
        throughput = 1000 / result['duration_seconds']
        
        # Should handle high throughput
        assert throughput > 500  # At least 500 logs/second
        assert result['memory_delta_mb'] < 20.0
        
        stats = exporter.get_stats()
        assert stats['logs_exported'] >= 1000
        
        await exporter.stop()


class TestOverallPerformance:
    """Test overall system performance."""
    
    def test_end_to_end_performance(self):
        """Test end-to-end performance."""
        # Test signature computation with caching
        computer = get_signature_computer()
        cache = get_signature_cache()
        pool = get_memory_pool()
        
        profiler = PerformanceProfiler()
        profiler.start()
        
        # Simulate realistic log processing
        messages = [
            "User {user_id} logged in from IP {ip}",
            "Database query executed in {duration}ms",
            "Error occurred: {error_type} after {timeout}s",
            "Cache hit for key {key}",
            "Request {request_id} processed successfully",
        ]
        
        for i in range(1000):
            # Generate realistic message
            message = messages[i % len(messages)].format(
                user_id=i,
                ip=f"192.168.1.{i % 255}",
                duration=i * 0.1,
                error_type="timeout" if i % 10 == 0 else "connection",
                timeout=i % 30,
                key=f"user:{i}",
                request_id=f"req_{i}",
            )
            
            # Compute signature
            signature = computer.compute_signature(message)
            
            # Use memory pool
            block = pool.get_block()
            block[:len(signature)] = signature.encode('utf-8')
            pool.return_block(block)
        
        result = profiler.stop()
        
        # Should be very efficient
        assert result['duration_seconds'] < 1.0
        assert result['memory_delta_mb'] < 5.0
        
        # Check cache efficiency
        cache_stats = cache.get_stats()
        assert cache_stats['hit_rate'] > 0.5
        
        # Check memory pool efficiency
        pool_stats = pool.get_stats()
        assert pool_stats['total_allocated'] <= 100


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])
