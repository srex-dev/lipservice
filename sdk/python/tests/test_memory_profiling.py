"""
Memory profiling and leak detection for LipService Python SDK
"""

import asyncio
import gc
import logging
import os
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any

import psutil

from lipservice import configure_adaptive_logging, get_logger, shutdown
from lipservice.sampler import AdaptiveSampler
from lipservice.signature import compute_signature

logger = logging.getLogger(__name__)


@dataclass
class MemoryProfile:
    """Memory profile snapshot"""
    timestamp: float
    rss_mb: float
    vms_mb: float
    heap_mb: float
    stack_mb: float
    gc_objects: int
    gc_collections: int


class MemoryProfiler:
    """Memory profiler for LipService SDK"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.profiles: list[MemoryProfile] = []
        self.tracemalloc_started = False

    def start_tracing(self):
        """Start memory tracing"""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True

    def stop_tracing(self):
        """Stop memory tracing"""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False

    def take_snapshot(self) -> MemoryProfile:
        """Take a memory profile snapshot"""
        memory_info = self.process.memory_info()
        gc_stats = gc.get_stats()

        profile = MemoryProfile(
            timestamp=time.time(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            heap_mb=memory_info.rss / 1024 / 1024,  # Approximate
            stack_mb=0,  # Not easily measurable
            gc_objects=len(gc.get_objects()),
            gc_collections=sum(stat['collections'] for stat in gc_stats)
        )

        self.profiles.append(profile)
        return profile

    def analyze_memory_growth(self) -> dict[str, Any]:
        """Analyze memory growth over time"""
        if len(self.profiles) < 2:
            return {"error": "Not enough profiles for analysis"}

        first_profile = self.profiles[0]
        last_profile = self.profiles[-1]

        rss_growth = last_profile.rss_mb - first_profile.rss_mb
        vms_growth = last_profile.vms_mb - first_profile.vms_mb
        objects_growth = last_profile.gc_objects - first_profile.gc_objects
        collections_growth = last_profile.gc_collections - first_profile.gc_collections

        # Calculate growth rate
        time_delta = last_profile.timestamp - first_profile.timestamp
        rss_growth_rate = rss_growth / time_delta if time_delta > 0 else 0

        return {
            "rss_growth_mb": rss_growth,
            "vms_growth_mb": vms_growth,
            "objects_growth": objects_growth,
            "collections_growth": collections_growth,
            "rss_growth_rate_mb_per_sec": rss_growth_rate,
            "time_delta_seconds": time_delta,
            "profiles_count": len(self.profiles)
        }

    def detect_memory_leaks(self, threshold_mb: float = 10.0) -> bool:
        """Detect potential memory leaks"""
        analysis = self.analyze_memory_growth()

        if "error" in analysis:
            return False

        # Check if memory growth exceeds threshold
        rss_growth = analysis["rss_growth_mb"]
        growth_rate = analysis["rss_growth_rate_mb_per_sec"]

        # Consider it a leak if:
        # 1. Total growth exceeds threshold
        # 2. Growth rate is positive and significant
        is_leak = (rss_growth > threshold_mb) or (growth_rate > 0.1)

        return is_leak

    def get_tracemalloc_stats(self) -> dict[str, Any] | None:
        """Get tracemalloc statistics"""
        if not self.tracemalloc_started:
            return None

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        return {
            "total_size_mb": sum(stat.size for stat in top_stats) / 1024 / 1024,
            "total_count": sum(stat.count for stat in top_stats),
            "top_allocations": [
                {
                    "filename": stat.traceback.format()[0],
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                }
                for stat in top_stats[:10]
            ]
        }


class MemoryLeakDetector:
    """Memory leak detector for LipService SDK"""

    def __init__(self):
        self.profiler = MemoryProfiler()

    async def test_logging_memory_leak(self, num_iterations: int = 1000) -> dict[str, Any]:
        """Test for memory leaks during logging"""

        logger.info(f"Starting logging memory leak test: {num_iterations} iterations")

        # Start memory tracing
        self.profiler.start_tracing()

        # Configure SDK
        await configure_adaptive_logging(
            service_name='memory-leak-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=300,
            pattern_report_interval=600,
        )

        sdk_logger = get_logger('memory-leak-test')

        # Take initial snapshot
        initial_profile = self.profiler.take_snapshot()

        # Perform logging iterations
        for i in range(num_iterations):
            await sdk_logger.info(f'Memory leak test message {i}', {'iteration': i})

            # Take snapshot every 100 iterations
            if i % 100 == 0:
                self.profiler.take_snapshot()

        # Take final snapshot
        final_profile = self.profiler.take_snapshot()

        # Analyze memory growth
        analysis = self.profiler.analyze_memory_growth()
        has_leak = self.profiler.detect_memory_leaks(threshold_mb=5.0)

        # Get tracemalloc stats
        tracemalloc_stats = self.profiler.get_tracemalloc_stats()

        # Cleanup
        await shutdown()
        self.profiler.stop_tracing()

        return {
            "test_name": "Logging Memory Leak",
            "iterations": num_iterations,
            "initial_memory_mb": initial_profile.rss_mb,
            "final_memory_mb": final_profile.rss_mb,
            "memory_growth_mb": analysis["rss_growth_mb"],
            "growth_rate_mb_per_sec": analysis["rss_growth_rate_mb_per_sec"],
            "has_leak": has_leak,
            "tracemalloc_stats": tracemalloc_stats,
            "analysis": analysis
        }

    async def test_sampler_memory_leak(self, num_iterations: int = 10000) -> dict[str, Any]:
        """Test for memory leaks in the sampler"""

        logger.info(f"Starting sampler memory leak test: {num_iterations} iterations")

        # Start memory tracing
        self.profiler.start_tracing()

        # Create sampler
        sampler = AdaptiveSampler(None)

        # Take initial snapshot
        initial_profile = self.profiler.take_snapshot()

        # Perform sampling iterations
        for i in range(num_iterations):
            message = f'Test message {i}'
            severity = ['INFO', 'WARNING', 'ERROR', 'DEBUG'][i % 4]
            sampler.should_sample(message, severity)

            # Take snapshot every 1000 iterations
            if i % 1000 == 0:
                self.profiler.take_snapshot()

        # Take final snapshot
        final_profile = self.profiler.take_snapshot()

        # Analyze memory growth
        analysis = self.profiler.analyze_memory_growth()
        has_leak = self.profiler.detect_memory_leaks(threshold_mb=2.0)

        # Get tracemalloc stats
        tracemalloc_stats = self.profiler.get_tracemalloc_stats()

        # Cleanup
        self.profiler.stop_tracing()

        return {
            "test_name": "Sampler Memory Leak",
            "iterations": num_iterations,
            "initial_memory_mb": initial_profile.rss_mb,
            "final_memory_mb": final_profile.rss_mb,
            "memory_growth_mb": analysis["rss_growth_mb"],
            "growth_rate_mb_per_sec": analysis["rss_growth_rate_mb_per_sec"],
            "has_leak": has_leak,
            "tracemalloc_stats": tracemalloc_stats,
            "analysis": analysis
        }

    async def test_signature_memory_leak(self, num_iterations: int = 100000) -> dict[str, Any]:
        """Test for memory leaks in signature computation"""

        logger.info(f"Starting signature memory leak test: {num_iterations} iterations")

        # Start memory tracing
        self.profiler.start_tracing()

        # Take initial snapshot
        initial_profile = self.profiler.take_snapshot()

        # Perform signature computations
        for i in range(num_iterations):
            message = f'User {i} logged in from IP 192.168.1.{i % 255}'
            compute_signature(message)

            # Take snapshot every 10000 iterations
            if i % 10000 == 0:
                self.profiler.take_snapshot()

        # Take final snapshot
        final_profile = self.profiler.take_snapshot()

        # Analyze memory growth
        analysis = self.profiler.analyze_memory_growth()
        has_leak = self.profiler.detect_memory_leaks(threshold_mb=1.0)

        # Get tracemalloc stats
        tracemalloc_stats = self.profiler.get_tracemalloc_stats()

        # Cleanup
        self.profiler.stop_tracing()

        return {
            "test_name": "Signature Memory Leak",
            "iterations": num_iterations,
            "initial_memory_mb": initial_profile.rss_mb,
            "final_memory_mb": final_profile.rss_mb,
            "memory_growth_mb": analysis["rss_growth_mb"],
            "growth_rate_mb_per_sec": analysis["rss_growth_rate_mb_per_sec"],
            "has_leak": has_leak,
            "tracemalloc_stats": tracemalloc_stats,
            "analysis": analysis
        }

    async def test_gc_pressure(self, num_iterations: int = 5000) -> dict[str, Any]:
        """Test garbage collection pressure"""

        logger.info(f"Starting GC pressure test: {num_iterations} iterations")

        # Configure SDK
        await configure_adaptive_logging(
            service_name='gc-pressure-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=300,
            pattern_report_interval=600,
        )

        sdk_logger = get_logger('gc-pressure-test')

        # Get initial GC stats
        initial_gc_stats = gc.get_stats()
        initial_gc_count = gc.get_count()

        # Perform operations that create temporary objects
        for i in range(num_iterations):
            # Create temporary objects
            temp_data = {
                'iteration': i,
                'timestamp': time.time(),
                'random_data': [j for j in range(100)],
                'nested_data': {
                    'level1': {
                        'level2': {
                            'level3': f'value_{i}'
                        }
                    }
                }
            }

            await sdk_logger.info(f'GC pressure test {i}', temp_data)

            # Force GC every 1000 iterations
            if i % 1000 == 0:
                gc.collect()

        # Get final GC stats
        final_gc_stats = gc.get_stats()
        final_gc_count = gc.get_count()

        # Calculate GC pressure
        gc_pressure = {
            "initial_stats": initial_gc_stats,
            "final_stats": final_gc_stats,
            "initial_count": initial_gc_count,
            "final_count": final_gc_count,
            "collections_increase": [
                final_gc_count[i] - initial_gc_count[i]
                for i in range(len(initial_gc_count))
            ],
            "total_collections": sum(final_gc_count) - sum(initial_gc_count)
        }

        # Cleanup
        await shutdown()

        return {
            "test_name": "GC Pressure Test",
            "iterations": num_iterations,
            "gc_pressure": gc_pressure,
            "collections_per_iteration": gc_pressure["total_collections"] / num_iterations
        }

    def print_memory_report(self, results: list[dict[str, Any]]):
        """Print memory profiling report"""

        print("\n" + "="*80)
        print("LIPSERVICE SDK MEMORY PROFILING REPORT")
        print("="*80)

        for result in results:
            print(f"\n{result['test_name']}")
            print("-" * len(result['test_name']))
            print(f"Iterations: {result['iterations']:,}")

            if 'initial_memory_mb' in result:
                print(f"Initial Memory: {result['initial_memory_mb']:.2f}MB")
                print(f"Final Memory: {result['final_memory_mb']:.2f}MB")
                print(f"Memory Growth: {result['memory_growth_mb']:.2f}MB")
                print(f"Growth Rate: {result['growth_rate_mb_per_sec']:.4f}MB/sec")
                print(f"Has Leak: {'❌ YES' if result['has_leak'] else '✅ NO'}")

            if 'gc_pressure' in result:
                print(f"Total GC Collections: {result['gc_pressure']['total_collections']}")
                print(f"Collections per Iteration: {result['collections_per_iteration']:.4f}")

            if 'tracemalloc_stats' in result and result['tracemalloc_stats']:
                stats = result['tracemalloc_stats']
                print(f"Total Allocated: {stats['total_size_mb']:.2f}MB")
                print(f"Total Objects: {stats['total_count']:,}")

                if stats['top_allocations']:
                    print("Top Allocations:")
                    for alloc in stats['top_allocations'][:5]:
                        print(f"  {alloc['filename']}: {alloc['size_mb']:.2f}MB ({alloc['count']:,} objects)")

        # Overall assessment
        print(f"\n{'='*80}")
        print("MEMORY ASSESSMENT")
        print(f"{'='*80}")

        leaks_found = any(result.get('has_leak', False) for result in results)

        if not leaks_found:
            print("✅ No memory leaks detected")
        else:
            print("❌ Potential memory leaks detected")

        # Check GC pressure
        gc_results = [r for r in results if 'gc_pressure' in r]
        if gc_results:
            avg_collections = sum(r['collections_per_iteration'] for r in gc_results) / len(gc_results)
            if avg_collections < 0.01:
                print("✅ Low GC pressure")
            elif avg_collections < 0.1:
                print("⚠️ Moderate GC pressure")
            else:
                print("❌ High GC pressure")


async def run_memory_profiling():
    """Run comprehensive memory profiling"""

    print("🔍 Starting LipService SDK Memory Profiling")
    print("="*60)

    detector = MemoryLeakDetector()
    results = []

    try:
        # Run memory leak tests
        print("\n📝 Testing logging memory leaks...")
        result1 = await detector.test_logging_memory_leak(1000)
        results.append(result1)

        print("\n🎯 Testing sampler memory leaks...")
        result2 = await detector.test_sampler_memory_leak(10000)
        results.append(result2)

        print("\n🔍 Testing signature memory leaks...")
        result3 = await detector.test_signature_memory_leak(100000)
        results.append(result3)

        print("\n🗑️ Testing GC pressure...")
        result4 = await detector.test_gc_pressure(5000)
        results.append(result4)

        # Print report
        detector.print_memory_report(results)

    except Exception as e:
        print(f"❌ Memory profiling failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_memory_profiling())
