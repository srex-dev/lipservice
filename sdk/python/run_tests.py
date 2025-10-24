#!/usr/bin/env python3
"""
Comprehensive test runner for LipService Python SDK
"""

import argparse
import asyncio
import subprocess
import sys
import time
from typing import Any


class TestRunner:
    """Comprehensive test runner for LipService SDK"""

    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.start_time = time.time()

    async def run_unit_tests(self) -> dict[str, Any]:
        """Run unit tests"""
        print("🧪 Running Unit Tests...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/test_*.py',
                '-v',
                '--tb=short',
                '--disable-warnings'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Unit Tests',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Unit Tests',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_integration_tests(self) -> dict[str, Any]:
        """Run integration tests"""
        print("🔗 Running Integration Tests...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/test_integration.py',
                '-v',
                '--tb=short',
                '--disable-warnings'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Integration Tests',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Integration Tests',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_performance_tests(self) -> dict[str, Any]:
        """Run performance tests"""
        print("⚡ Running Performance Tests...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable,
                'tests/test_performance.py'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Performance Tests',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Performance Tests',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_memory_tests(self) -> dict[str, Any]:
        """Run memory profiling tests"""
        print("💾 Running Memory Profiling Tests...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable,
                'tests/test_memory_profiling.py'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Memory Profiling',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Memory Profiling',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_coverage_tests(self) -> dict[str, Any]:
        """Run tests with coverage"""
        print("📊 Running Coverage Tests...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/test_*.py',
                '--cov=lipservice',
                '--cov-report=html',
                '--cov-report=term-missing',
                '--cov-report=xml',
                '-v',
                '--disable-warnings'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Coverage Tests',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Coverage Tests',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_linting(self) -> dict[str, Any]:
        """Run code linting"""
        print("🔍 Running Code Linting...")

        start_time = time.time()

        try:
            # Run flake8
            flake8_result = subprocess.run([
                sys.executable, '-m', 'flake8',
                'lipservice/',
                'tests/',
                '--max-line-length=100',
                '--ignore=E203,W503'
            ], capture_output=True, text=True, cwd='sdk/python')

            # Run black check
            black_result = subprocess.run([
                sys.executable, '-m', 'black',
                '--check',
                'lipservice/',
                'tests/'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            success = flake8_result.returncode == 0 and black_result.returncode == 0

            return {
                'test_type': 'Code Linting',
                'success': success,
                'duration': duration,
                'flake8_stdout': flake8_result.stdout,
                'flake8_stderr': flake8_result.stderr,
                'black_stdout': black_result.stdout,
                'black_stderr': black_result.stderr,
                'flake8_returncode': flake8_result.returncode,
                'black_returncode': black_result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Code Linting',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def run_type_checking(self) -> dict[str, Any]:
        """Run type checking"""
        print("🔍 Running Type Checking...")

        start_time = time.time()

        try:
            result = subprocess.run([
                sys.executable, '-m', 'mypy',
                'lipservice/',
                '--ignore-missing-imports',
                '--no-strict-optional'
            ], capture_output=True, text=True, cwd='sdk/python')

            duration = time.time() - start_time

            return {
                'test_type': 'Type Checking',
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_type': 'Type Checking',
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    def print_results(self):
        """Print test results summary"""

        total_duration = time.time() - self.start_time

        print("\n" + "="*80)
        print("LIPSERVICE SDK TEST RESULTS SUMMARY")
        print("="*80)

        successful_tests = sum(1 for result in self.results if result['success'])
        total_tests = len(self.results)

        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")

        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")

        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test_type']:<20} ({result['duration']:.2f}s)")

            if not result['success'] and 'error' in result:
                print(f"    Error: {result['error']}")

        # Overall assessment
        print(f"\n{'='*80}")
        print("OVERALL ASSESSMENT")
        print(f"{'='*80}")

        if successful_tests == total_tests:
            print("🎉 ALL TESTS PASSED! SDK is ready for production.")
        elif successful_tests >= total_tests * 0.8:
            print("⚠️ Most tests passed. Review failed tests before production.")
        else:
            print("❌ Multiple test failures. SDK needs fixes before production.")

        # Recommendations
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print(f"{'='*80}")

        failed_tests = [r for r in self.results if not r['success']]

        if not failed_tests:
            print("✅ No issues found. SDK is production-ready!")
        else:
            print("🔧 Issues to address:")
            for result in failed_tests:
                print(f"  - {result['test_type']}: {result.get('error', 'See output above')}")

    async def run_all_tests(self, include_performance: bool = True, include_memory: bool = True):
        """Run all tests"""

        print("🚀 Starting Comprehensive LipService SDK Testing")
        print("="*60)

        # Always run these tests
        self.results.append(await self.run_unit_tests())
        self.results.append(await self.run_integration_tests())
        self.results.append(await self.run_coverage_tests())
        self.results.append(await self.run_linting())
        self.results.append(await self.run_type_checking())

        # Optional tests
        if include_performance:
            self.results.append(await self.run_performance_tests())

        if include_memory:
            self.results.append(await self.run_memory_tests())

        # Print results
        self.print_results()


async def main():
    """Main test runner"""

    parser = argparse.ArgumentParser(description='LipService SDK Test Runner')
    parser.add_argument('--no-performance', action='store_true',
                       help='Skip performance tests')
    parser.add_argument('--no-memory', action='store_true',
                       help='Skip memory profiling tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run only essential tests (unit, integration, linting)')

    args = parser.parse_args()

    runner = TestRunner()

    if args.quick:
        # Quick test run
        runner.results.append(await runner.run_unit_tests())
        runner.results.append(await runner.run_integration_tests())
        runner.results.append(await runner.run_linting())
        runner.print_results()
    else:
        # Full test run
        await runner.run_all_tests(
            include_performance=not args.no_performance,
            include_memory=not args.no_memory
        )


if __name__ == "__main__":
    asyncio.run(main())
