"""
Performance benchmarking for LipService Python SDK
"""

import asyncio
import logging
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any

import psutil

from lipservice import configure_adaptive_logging, get_logger, shutdown
from lipservice.sampler import AdaptiveSampler
from lipservice.signature import compute_signature

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark"""
    test_name: str
    duration: float
    operations: int
    operations_per_second: float
    average_latency: float
    p95_latency: float
    p99_latency: float
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceBenchmark:
    """Performance benchmarking suite for LipService SDK"""

    def __init__(self):
        self.results: list[BenchmarkResult] = []
        self.process = psutil.Process(os.getpid())

    async def benchmark_logging_performance(self,
                                          num_logs: int = 10000,
                                          concurrent_tasks: int = 10) -> BenchmarkResult:
        """Benchmark logging performance"""

        logger.info(f"Starting logging performance benchmark: {num_logs} logs, {concurrent_tasks} concurrent tasks")

        # Configure SDK
        await configure_adaptive_logging(
            service_name='benchmark-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=300,  # Long interval to avoid interference
            pattern_report_interval=600,
        )

        sdk_logger = get_logger('benchmark-test')

        # Measure initial memory and CPU
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_cpu = self.process.cpu_percent()

        # Prepare test data
        test_messages = [f'Benchmark message {i}' for i in range(num_logs)]
        test_attributes = [{'iteration': i, 'test': 'benchmark'} for i in range(num_logs)]

        # Benchmark logging
        start_time = time.time()
        latencies = []

        async def log_worker(worker_id: int, messages: list[str], attrs: list[dict[str, Any]]):
            """Worker function for concurrent logging"""
            worker_latencies = []

            for i, (message, attr) in enumerate(zip(messages, attrs)):
                log_start = time.time()
                await sdk_logger.info(message, attr)
                log_end = time.time()
                worker_latencies.append(log_end - log_start)

            return worker_latencies

        # Split work among concurrent tasks
        logs_per_task = num_logs // concurrent_tasks
        tasks = []

        for i in range(concurrent_tasks):
            start_idx = i * logs_per_task
            end_idx = start_idx + logs_per_task if i < concurrent_tasks - 1 else num_logs

            task_messages = test_messages[start_idx:end_idx]
            task_attrs = test_attributes[start_idx:end_idx]

            tasks.append(log_worker(i, task_messages, task_attrs))

        # Run concurrent logging
        task_results = await asyncio.gather(*tasks)

        # Aggregate latencies
        for task_latencies in task_results:
            latencies.extend(task_latencies)

        end_time = time.time()
        duration = end_time - start_time

        # Measure final memory and CPU
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_cpu = self.process.cpu_percent()

        # Calculate statistics
        operations_per_second = num_logs / duration
        average_latency = statistics.mean(latencies)
        p95_latency = self._percentile(latencies, 95)
        p99_latency = self._percentile(latencies, 99)
        memory_usage = final_memory - initial_memory
        cpu_usage = final_cpu - initial_cpu

        result = BenchmarkResult(
            test_name="Logging Performance",
            duration=duration,
            operations=num_logs,
            operations_per_second=operations_per_second,
            average_latency=average_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )

        self.results.append(result)

        # Cleanup
        await shutdown()

        return result

    async def benchmark_signature_computation(self, num_signatures: int = 100000) -> BenchmarkResult:
        """Benchmark signature computation performance"""

        logger.info(f"Starting signature computation benchmark: {num_signatures} signatures")

        # Prepare test messages
        test_messages = []
        for i in range(num_signatures // 5):
            test_messages.extend([
                f'User {i} logged in from IP 192.168.1.{i % 255}',
                f'Database query executed in {i * 0.1:.2f}ms',
                f'Cache hit for key user:{i}',
                f'Error occurred: Connection timeout after {i}ms',
                f'Request {i} processed successfully',
            ])

        # Measure initial memory and CPU
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_cpu = self.process.cpu_percent()

        # Benchmark signature computation
        start_time = time.time()
        latencies = []

        for message in test_messages:
            sig_start = time.time()
            compute_signature(message)
            sig_end = time.time()
            latencies.append(sig_end - sig_start)

        end_time = time.time()
        duration = end_time - start_time

        # Measure final memory and CPU
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_cpu = self.process.cpu_percent()

        # Calculate statistics
        operations_per_second = num_signatures / duration
        average_latency = statistics.mean(latencies)
        p95_latency = self._percentile(latencies, 95)
        p99_latency = self._percentile(latencies, 99)
        memory_usage = final_memory - initial_memory
        cpu_usage = final_cpu - initial_cpu

        result = BenchmarkResult(
            test_name="Signature Computation",
            duration=duration,
            operations=num_signatures,
            operations_per_second=operations_per_second,
            average_latency=average_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )

        self.results.append(result)
        return result

    async def benchmark_sampling_decisions(self, num_decisions: int = 100000) -> BenchmarkResult:
        """Benchmark sampling decision performance"""

        logger.info(f"Starting sampling decision benchmark: {num_decisions} decisions")

        # Create sampler
        sampler = AdaptiveSampler(None)  # No client needed for this test

        # Prepare test data
        test_messages = [f'Test message {i}' for i in range(num_decisions)]
        test_severities = ['INFO', 'WARNING', 'ERROR', 'DEBUG'] * (num_decisions // 4)

        # Measure initial memory and CPU
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_cpu = self.process.cpu_percent()

        # Benchmark sampling decisions
        start_time = time.time()
        latencies = []

        for message, severity in zip(test_messages, test_severities):
            decision_start = time.time()
            sampler.should_sample(message, severity)
            decision_end = time.time()
            latencies.append(decision_end - decision_start)

        end_time = time.time()
        duration = end_time - start_time

        # Measure final memory and CPU
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_cpu = self.process.cpu_percent()

        # Calculate statistics
        operations_per_second = num_decisions / duration
        average_latency = statistics.mean(latencies)
        p95_latency = self._percentile(latencies, 95)
        p99_latency = self._percentile(latencies, 99)
        memory_usage = final_memory - initial_memory
        cpu_usage = final_cpu - initial_cpu

        result = BenchmarkResult(
            test_name="Sampling Decisions",
            duration=duration,
            operations=num_decisions,
            operations_per_second=operations_per_second,
            average_latency=average_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )

        self.results.append(result)
        return result

    async def benchmark_memory_efficiency(self, num_logs: int = 50000) -> BenchmarkResult:
        """Benchmark memory efficiency during extended logging"""

        logger.info(f"Starting memory efficiency benchmark: {num_logs} logs")

        # Configure SDK
        await configure_adaptive_logging(
            service_name='memory-benchmark-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=300,
            pattern_report_interval=600,
        )

        sdk_logger = get_logger('memory-benchmark-test')

        # Measure initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # Log messages in batches to monitor memory growth
        batch_size = 1000
        latencies = []

        start_time = time.time()

        for batch_start in range(0, num_logs, batch_size):
            batch_end = min(batch_start + batch_size, num_logs)

            for i in range(batch_start, batch_end):
                log_start = time.time()
                await sdk_logger.info(f'Memory test message {i}', {'iteration': i})
                log_end = time.time()
                latencies.append(log_end - log_start)

            # Check memory usage after each batch
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory

            logger.info(f"Batch {batch_start}-{batch_end}: Memory growth: {memory_growth:.2f}MB")

        end_time = time.time()
        duration = end_time - start_time

        # Measure final memory
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_usage = final_memory - initial_memory

        # Calculate statistics
        operations_per_second = num_logs / duration
        average_latency = statistics.mean(latencies)
        p95_latency = self._percentile(latencies, 95)
        p99_latency = self._percentile(latencies, 99)

        result = BenchmarkResult(
            test_name="Memory Efficiency",
            duration=duration,
            operations=num_logs,
            operations_per_second=operations_per_second,
            average_latency=average_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0  # Not measured for this test
        )

        self.results.append(result)

        # Cleanup
        await shutdown()

        return result

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    def print_results(self):
        """Print all benchmark results"""
        print("\n" + "="*80)
        print("LIPSERVICE SDK PERFORMANCE BENCHMARKS")
        print("="*80)

        for result in self.results:
            print(f"\n{result.test_name}")
            print("-" * len(result.test_name))
            print(f"Duration: {result.duration:.2f} seconds")
            print(f"Operations: {result.operations:,}")
            print(f"Operations/Second: {result.operations_per_second:,.0f}")
            print(f"Average Latency: {result.average_latency:.6f}s")
            print(f"95th Percentile: {result.p95_latency:.6f}s")
            print(f"99th Percentile: {result.p99_latency:.6f}s")
            print(f"Memory Usage: {result.memory_usage_mb:.2f}MB")
            if result.cpu_usage_percent > 0:
                print(f"CPU Usage: {result.cpu_usage_percent:.1f}%")

        # Performance assessment
        print(f"\n{'='*80}")
        print("PERFORMANCE ASSESSMENT")
        print(f"{'='*80}")

        logging_result = next((r for r in self.results if r.test_name == "Logging Performance"), None)
        if logging_result:
            if logging_result.operations_per_second > 1000:
                print("✅ Logging Performance: EXCELLENT (>1000 ops/sec)")
            elif logging_result.operations_per_second > 500:
                print("✅ Logging Performance: GOOD (>500 ops/sec)")
            else:
                print("❌ Logging Performance: NEEDS IMPROVEMENT (<500 ops/sec)")

        signature_result = next((r for r in self.results if r.test_name == "Signature Computation"), None)
        if signature_result:
            if signature_result.operations_per_second > 100000:
                print("✅ Signature Computation: EXCELLENT (>100K ops/sec)")
            elif signature_result.operations_per_second > 50000:
                print("✅ Signature Computation: GOOD (>50K ops/sec)")
            else:
                print("❌ Signature Computation: NEEDS IMPROVEMENT (<50K ops/sec)")

        sampling_result = next((r for r in self.results if r.test_name == "Sampling Decisions"), None)
        if sampling_result:
            if sampling_result.operations_per_second > 100000:
                print("✅ Sampling Decisions: EXCELLENT (>100K ops/sec)")
            elif sampling_result.operations_per_second > 50000:
                print("✅ Sampling Decisions: GOOD (>50K ops/sec)")
            else:
                print("❌ Sampling Decisions: NEEDS IMPROVEMENT (<50K ops/sec)")

        memory_result = next((r for r in self.results if r.test_name == "Memory Efficiency"), None)
        if memory_result:
            memory_per_log = memory_result.memory_usage_mb / memory_result.operations * 1024  # KB per log
            if memory_per_log < 1:
                print("✅ Memory Efficiency: EXCELLENT (<1KB per log)")
            elif memory_per_log < 5:
                print("✅ Memory Efficiency: GOOD (<5KB per log)")
            else:
                print("❌ Memory Efficiency: NEEDS IMPROVEMENT (>5KB per log)")


async def run_performance_benchmarks():
    """Run all performance benchmarks"""

    print("🚀 Starting LipService SDK Performance Benchmarks")
    print("="*60)

    benchmark = PerformanceBenchmark()

    try:
        # Run benchmarks
        print("\n📝 Running Logging Performance Benchmark...")
        await benchmark.benchmark_logging_performance(num_logs=10000, concurrent_tasks=10)

        print("\n🔍 Running Signature Computation Benchmark...")
        await benchmark.benchmark_signature_computation(num_signatures=100000)

        print("\n🎯 Running Sampling Decision Benchmark...")
        await benchmark.benchmark_sampling_decisions(num_decisions=100000)

        print("\n💾 Running Memory Efficiency Benchmark...")
        await benchmark.benchmark_memory_efficiency(num_logs=20000)

        # Print results
        benchmark.print_results()

    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_performance_benchmarks())
