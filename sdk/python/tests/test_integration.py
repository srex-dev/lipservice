"""
Integration tests for LipService Python SDK
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from lipservice import configure_adaptive_logging, get_logger, shutdown


class TestSDKIntegration:
    """Integration tests for the complete SDK workflow"""

    @pytest.fixture
    async def mock_lipservice_backend(self):
        """Mock LipService backend for testing"""
        with patch('lipservice.client.LipServiceClient') as mock_client:
            # Mock policy response
            mock_policy = {
                'version': 1,
                'global_rate': 0.3,
                'severity_rates': {'DEBUG': 0.05, 'INFO': 0.2, 'ERROR': 1.0},
                'pattern_rates': {},
                'anomaly_boost': 2.0,
                'reasoning': 'Test policy for integration testing'
            }

            mock_client_instance = AsyncMock()
            mock_client_instance.getActivePolicy.return_value = mock_policy
            mock_client_instance.reportPatterns.return_value = True

            mock_client.return_value = mock_client_instance
            yield mock_client_instance

    @pytest.fixture
    async def mock_posthog_backend(self):
        """Mock PostHog backend for testing"""
        with patch('lipservice.posthog.PostHogOTLPExporter') as mock_exporter:
            mock_exporter_instance = AsyncMock()
            mock_exporter_instance.start.return_value = None
            mock_exporter_instance.stop.return_value = None
            mock_exporter_instance.exportLog.return_value = None

            mock_exporter.return_value = mock_exporter_instance
            yield mock_exporter_instance

    @pytest.mark.asyncio
    async def test_complete_sdk_workflow(self, mock_lipservice_backend, mock_posthog_backend):
        """Test complete SDK workflow from configuration to logging"""

        # Configure SDK
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

        # Test different log levels
        logger.info('User logged in', user_id=123)
        logger.warning('High memory usage', usage=85)
        logger.error('Database connection failed', error='timeout')
        logger.debug('Cache hit', key='user:123')

        # Wait for background tasks
        await asyncio.sleep(0.1)

        # Verify policy was fetched
        mock_lipservice_backend.getActivePolicy.assert_called()

        # Verify patterns were reported
        await asyncio.sleep(2.5)  # Wait for pattern reporting
        mock_lipservice_backend.reportPatterns.assert_called()

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_sdk_without_posthog(self, mock_lipservice_backend):
        """Test SDK functionality without PostHog integration"""

        # Configure SDK without PostHog
        configure_adaptive_logging(
            service_name='no-posthog-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=1,
            pattern_report_interval=2,
        )

        logger = get_logger('no-posthog-test')

        # Test logging
        logger.info('Test message', test='value')
        logger.error('Test error', error='test')

        # Wait for background tasks
        await asyncio.sleep(0.1)

        # Verify policy was fetched
        mock_lipservice_backend.getActivePolicy.assert_called()

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_sdk_error_handling(self, mock_lipservice_backend):
        """Test SDK error handling and graceful degradation"""

        # Mock backend errors
        mock_lipservice_backend.getActivePolicy.side_effect = Exception('Backend error')
        mock_lipservice_backend.reportPatterns.side_effect = Exception('Report error')

        # Configure SDK
        configure_adaptive_logging(
            service_name='error-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=1,
            pattern_report_interval=2,
        )

        logger = get_logger('error-test')

        # Test logging (should work even with backend errors)
        logger.info('Test message', test='value')
        logger.error('Test error', error='test')

        # Wait for background tasks
        await asyncio.sleep(0.1)

        # Verify errors were handled gracefully
        assert mock_lipservice_backend.getActivePolicy.called

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_logging(self, mock_lipservice_backend):
        """Test concurrent logging from multiple threads"""

        # Configure SDK
        configure_adaptive_logging(
            service_name='concurrent-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=1,
            pattern_report_interval=2,
        )

        logger = get_logger('concurrent-test')

        # Create multiple concurrent logging tasks
        async def log_worker(worker_id: int, count: int):
            for i in range(count):
                await logger.info(f'Worker {worker_id} message {i}', {'worker': worker_id, 'message': i})
                await asyncio.sleep(0.001)  # Small delay

        # Run concurrent workers
        tasks = [log_worker(i, 10) for i in range(5)]
        await asyncio.gather(*tasks)

        # Wait for background tasks
        await asyncio.sleep(0.1)

        # Verify policy was fetched
        mock_lipservice_backend.getActivePolicy.assert_called()

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_sdk_shutdown(self, mock_lipservice_backend):
        """Test SDK shutdown and cleanup"""

        # Configure SDK
        configure_adaptive_logging(
            service_name='shutdown-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=1,
            pattern_report_interval=2,
        )

        logger = get_logger('shutdown-test')

        # Log some messages
        await logger.info('Before shutdown', {'test': 'value'})

        # Shutdown SDK
        await shutdown()

        # Try to log after shutdown (should not crash)
        await logger.info('After shutdown', {'test': 'value'})

        # Verify shutdown was called
        mock_lipservice_backend.close.assert_called()


class TestPerformanceIntegration:
    """Performance integration tests"""

    @pytest.mark.asyncio
    async def test_high_volume_logging(self, mock_lipservice_backend):
        """Test high volume logging performance"""

        # Configure SDK
        configure_adaptive_logging(
            service_name='performance-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=10,
            pattern_report_interval=20,
        )

        logger = get_logger('performance-test')

        # Measure logging performance
        start_time = time.time()

        # Log 1000 messages
        for i in range(1000):
            await logger.info(f'Performance test message {i}', {'iteration': i})

        end_time = time.time()
        duration = end_time - start_time

        # Verify performance (should be fast)
        assert duration < 5.0  # Should complete in under 5 seconds
        assert 1000 / duration > 200  # Should handle >200 logs/second

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_memory_usage(self, mock_lipservice_backend):
        """Test memory usage during logging"""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Configure SDK
        configure_adaptive_logging(
            service_name='memory-test',
            lipservice_url='http://localhost:8000',
            policy_refresh_interval=10,
            pattern_report_interval=20,
        )

        logger = get_logger('memory-test')

        # Log many messages
        for i in range(1000):
            await logger.info(f'Memory test message {i}', {'iteration': i})

        # Check memory usage
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50 * 1024 * 1024

        # Cleanup
        await shutdown()


class TestEdgeCases:
    """Edge case testing"""

    @pytest.mark.asyncio
    async def test_empty_messages(self, mock_lipservice_backend):
        """Test handling of empty messages"""

        configure_adaptive_logging(
            service_name='edge-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('edge-test')

        # Test empty message
        await logger.info('', {})

        # Test None message
        await logger.info(None, {})

        # Test very long message
        long_message = 'x' * 10000
        await logger.info(long_message, {})

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_special_characters(self, mock_lipservice_backend):
        """Test handling of special characters in messages"""

        configure_adaptive_logging(
            service_name='special-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('special-test')

        # Test various special characters
        special_messages = [
            'Message with émojis 🚀',
            'Message with "quotes"',
            'Message with \'apostrophes\'',
            'Message with\nnewlines',
            'Message with\ttabs',
            'Message with unicode: 你好世界',
            'Message with symbols: !@#$%^&*()',
        ]

        for message in special_messages:
            await logger.info(message, {'special': True})

        # Cleanup
        await shutdown()

    @pytest.mark.asyncio
    async def test_large_attributes(self, mock_lipservice_backend):
        """Test handling of large attribute dictionaries"""

        configure_adaptive_logging(
            service_name='large-attr-test',
            lipservice_url='http://localhost:8000',
        )

        logger = get_logger('large-attr-test')

        # Test large attributes
        large_attrs = {f'key_{i}': f'value_{i}' for i in range(1000)}
        await logger.info('Large attributes test', large_attrs)

        # Test nested attributes
        nested_attrs = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': 'deep_value'
                    }
                }
            }
        }
        await logger.info('Nested attributes test', nested_attrs)

        # Cleanup
        await shutdown()


class TestFrameworkIntegration:
    """Framework integration tests"""

    @pytest.mark.asyncio
    async def test_django_integration(self, mock_lipservice_backend):
        """Test Django framework integration"""

        # Mock Django settings
        with patch.dict('os.environ', {'DJANGO_SETTINGS_MODULE': 'test_settings'}):
            with patch('django.conf.settings') as mock_settings:
                mock_settings.configure.return_value = None

                # Configure SDK
                configure_adaptive_logging(
                    service_name='django-test',
                    lipservice_url='http://localhost:8000',
                )

                logger = get_logger('django-test')
                await logger.info('Django integration test', {'framework': 'django'})

                # Cleanup
                await shutdown()

    @pytest.mark.asyncio
    async def test_fastapi_integration(self, mock_lipservice_backend):
        """Test FastAPI framework integration"""

        # Mock FastAPI
        with patch('fastapi.FastAPI') as mock_fastapi:
            mock_app = Mock()
            mock_fastapi.return_value = mock_app

            # Configure SDK
            configure_adaptive_logging(
                service_name='fastapi-test',
                lipservice_url='http://localhost:8000',
            )

            logger = get_logger('fastapi-test')
            await logger.info('FastAPI integration test', {'framework': 'fastapi'})

            # Cleanup
            await shutdown()

    @pytest.mark.asyncio
    async def test_flask_integration(self, mock_lipservice_backend):
        """Test Flask framework integration"""

        # Mock Flask
        with patch('flask.Flask') as mock_flask:
            mock_app = Mock()
            mock_flask.return_value = mock_app

            # Configure SDK
            configure_adaptive_logging(
                service_name='flask-test',
                lipservice_url='http://localhost:8000',
            )

            logger = get_logger('flask-test')
            await logger.info('Flask integration test', {'framework': 'flask'})

            # Cleanup
            await shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
