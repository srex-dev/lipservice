"""
Load testing framework for LipService
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Result of a load test"""
    test_name: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class LoadTester:
    """Load testing framework for LipService"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_log_ingestion(self, 
                                service_name: str, 
                                concurrent_users: int = 10,
                                requests_per_user: int = 100,
                                duration_seconds: int = 60) -> LoadTestResult:
        """Test log ingestion performance"""
        
        logger.info(f"Starting log ingestion test: {concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        async def user_session(user_id: int):
            """Simulate a user session"""
            user_response_times = []
            user_errors = []
            user_successful = 0
            user_failed = 0
            
            for i in range(requests_per_user):
                try:
                    # Generate test log data
                    log_data = {
                        'message': f'User {user_id} performed action {i}',
                        'level': 'INFO',
                        'timestamp': datetime.utcnow().isoformat(),
                        'attributes': {
                            'user_id': user_id,
                            'action_id': i,
                            'session_id': f'session_{user_id}_{i}',
                            'request_id': f'req_{user_id}_{i}',
                        }
                    }
                    
                    request_start = time.time()
                    
                    async with self.session.post(
                        f'{self.base_url}/api/v1/logs/{service_name}',
                        json=log_data
                    ) as response:
                        request_end = time.time()
                        response_time = request_end - request_start
                        
                        if response.status == 200:
                            user_successful += 1
                            user_response_times.append(response_time)
                        else:
                            user_failed += 1
                            user_errors.append(f'HTTP {response.status}: {await response.text()}')
                            
                except Exception as e:
                    user_failed += 1
                    user_errors.append(f'Exception: {str(e)}')
                
                # Small delay between requests
                await asyncio.sleep(0.01)
            
            return user_response_times, user_errors, user_successful, user_failed
        
        # Run concurrent user sessions
        tasks = [user_session(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for user_response_times, user_errors, user_successful, user_failed in results:
            response_times.extend(user_response_times)
            errors.extend(user_errors)
            successful_requests += user_successful
            failed_requests += user_failed
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        if response_times:
            average_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            average_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        total_requests = successful_requests + failed_requests
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return LoadTestResult(
            test_name="Log Ingestion",
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]  # Limit to first 10 errors
        )

    async def test_policy_fetch(self, 
                               service_name: str, 
                               concurrent_users: int = 50,
                               requests_per_user: int = 20) -> LoadTestResult:
        """Test policy fetching performance"""
        
        logger.info(f"Starting policy fetch test: {concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        async def fetch_policy(user_id: int):
            """Fetch policy for a user"""
            user_response_times = []
            user_errors = []
            user_successful = 0
            user_failed = 0
            
            for i in range(requests_per_user):
                try:
                    request_start = time.time()
                    
                    async with self.session.get(
                        f'{self.base_url}/api/v1/policies/{service_name}'
                    ) as response:
                        request_end = time.time()
                        response_time = request_end - request_start
                        
                        if response.status == 200:
                            user_successful += 1
                            user_response_times.append(response_time)
                        else:
                            user_failed += 1
                            user_errors.append(f'HTTP {response.status}: {await response.text()}')
                            
                except Exception as e:
                    user_failed += 1
                    user_errors.append(f'Exception: {str(e)}')
                
                # Small delay between requests
                await asyncio.sleep(0.05)
            
            return user_response_times, user_errors, user_successful, user_failed
        
        # Run concurrent policy fetches
        tasks = [fetch_policy(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for user_response_times, user_errors, user_successful, user_failed in results:
            response_times.extend(user_response_times)
            errors.extend(user_errors)
            successful_requests += user_successful
            failed_requests += user_failed
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        if response_times:
            average_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            average_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        total_requests = successful_requests + failed_requests
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return LoadTestResult(
            test_name="Policy Fetch",
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]
        )

    async def test_pattern_reporting(self, 
                                   service_name: str, 
                                   concurrent_users: int = 20,
                                   requests_per_user: int = 10) -> LoadTestResult:
        """Test pattern reporting performance"""
        
        logger.info(f"Starting pattern reporting test: {concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        async def report_patterns(user_id: int):
            """Report patterns for a user"""
            user_response_times = []
            user_errors = []
            user_successful = 0
            user_failed = 0
            
            for i in range(requests_per_user):
                try:
                    # Generate test pattern data
                    pattern_data = {
                        'service_name': service_name,
                        'patterns': [
                            {
                                'signature': f'pattern_{user_id}_{i}',
                                'message_sample': f'Test message {user_id} {i}',
                                'count': 100 + i,
                                'severity_distribution': {'INFO': 80, 'WARNING': 15, 'ERROR': 5},
                                'first_seen': datetime.utcnow().isoformat(),
                                'last_seen': datetime.utcnow().isoformat(),
                            }
                        ]
                    }
                    
                    request_start = time.time()
                    
                    async with self.session.post(
                        f'{self.base_url}/api/v1/patterns/stats',
                        json=pattern_data
                    ) as response:
                        request_end = time.time()
                        response_time = request_end - request_start
                        
                        if response.status == 200:
                            user_successful += 1
                            user_response_times.append(response_time)
                        else:
                            user_failed += 1
                            user_errors.append(f'HTTP {response.status}: {await response.text()}')
                            
                except Exception as e:
                    user_failed += 1
                    user_errors.append(f'Exception: {str(e)}')
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            return user_response_times, user_errors, user_successful, user_failed
        
        # Run concurrent pattern reports
        tasks = [report_patterns(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for user_response_times, user_errors, user_successful, user_failed in results:
            response_times.extend(user_response_times)
            errors.extend(user_errors)
            successful_requests += user_successful
            failed_requests += user_failed
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        if response_times:
            average_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            average_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        total_requests = successful_requests + failed_requests
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return LoadTestResult(
            test_name="Pattern Reporting",
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]
        )

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    def print_result(self, result: LoadTestResult):
        """Print load test result"""
        print(f"\n{'='*60}")
        print(f"Load Test Result: {result.test_name}")
        print(f"{'='*60}")
        print(f"Duration: {result.duration:.2f} seconds")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful Requests: {result.successful_requests}")
        print(f"Failed Requests: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"Requests per Second: {result.requests_per_second:.2f}")
        print(f"Average Response Time: {result.average_response_time:.3f}s")
        print(f"Median Response Time: {result.median_response_time:.3f}s")
        print(f"95th Percentile: {result.p95_response_time:.3f}s")
        print(f"99th Percentile: {result.p99_response_time:.3f}s")
        
        if result.errors:
            print(f"\nFirst 5 Errors:")
            for error in result.errors[:5]:
                print(f"  - {error}")


async def run_load_tests(base_url: str, api_key: str, service_name: str):
    """Run comprehensive load tests"""
    
    print("🚀 Starting LipService Load Tests")
    print("="*60)
    
    async with LoadTester(base_url, api_key) as tester:
        # Test 1: Log Ingestion
        print("\n📝 Test 1: Log Ingestion Performance")
        result1 = await tester.test_log_ingestion(service_name, concurrent_users=10, requests_per_user=50)
        tester.print_result(result1)
        
        # Test 2: Policy Fetch
        print("\n📋 Test 2: Policy Fetch Performance")
        result2 = await tester.test_policy_fetch(service_name, concurrent_users=20, requests_per_user=10)
        tester.print_result(result2)
        
        # Test 3: Pattern Reporting
        print("\n📊 Test 3: Pattern Reporting Performance")
        result3 = await tester.test_pattern_reporting(service_name, concurrent_users=5, requests_per_user=5)
        tester.print_result(result3)
        
        # Summary
        print(f"\n{'='*60}")
        print("LOAD TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Log Ingestion RPS: {result1.requests_per_second:.2f}")
        print(f"Policy Fetch RPS: {result2.requests_per_second:.2f}")
        print(f"Pattern Reporting RPS: {result3.requests_per_second:.2f}")
        print(f"Overall Error Rate: {((result1.failed_requests + result2.failed_requests + result3.failed_requests) / (result1.total_requests + result2.total_requests + result3.total_requests) * 100):.2f}%")
        
        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        if result1.requests_per_second > 100 and result1.error_rate < 1:
            print("✅ Log Ingestion: EXCELLENT")
        elif result1.requests_per_second > 50 and result1.error_rate < 5:
            print("✅ Log Ingestion: GOOD")
        else:
            print("❌ Log Ingestion: NEEDS IMPROVEMENT")
            
        if result2.requests_per_second > 200 and result2.error_rate < 1:
            print("✅ Policy Fetch: EXCELLENT")
        elif result2.requests_per_second > 100 and result2.error_rate < 5:
            print("✅ Policy Fetch: GOOD")
        else:
            print("❌ Policy Fetch: NEEDS IMPROVEMENT")
            
        if result3.requests_per_second > 50 and result3.error_rate < 1:
            print("✅ Pattern Reporting: EXCELLENT")
        elif result3.requests_per_second > 25 and result3.error_rate < 5:
            print("✅ Pattern Reporting: GOOD")
        else:
            print("❌ Pattern Reporting: NEEDS IMPROVEMENT")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python load_test.py <base_url> <api_key> <service_name>")
        print("Example: python load_test.py http://localhost:8000 test-key my-service")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    service_name = sys.argv[3]
    
    asyncio.run(run_load_tests(base_url, api_key, service_name))
