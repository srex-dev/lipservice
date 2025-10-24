"""
Test configuration and fixtures for LipService SDK tests.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_lipservice_backend():
    """Mock LipService backend for testing."""
    backend = MagicMock()
    backend.getActivePolicy = AsyncMock(return_value={
        'policy_id': 'test-policy',
        'sampling_rate': 0.1,
        'patterns': ['error', 'warning'],
        'max_logs_per_minute': 100
    })
    backend.reportPattern = AsyncMock(return_value={'status': 'success'})
    backend.getPatterns = AsyncMock(return_value={
        'patterns': [
            {'pattern': 'error', 'count': 10},
            {'pattern': 'warning', 'count': 5}
        ]
    })
    return backend


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict('os.environ', {
        'LIPSERVICE_URL': 'http://localhost:8000',
        'LIPSERVICE_API_KEY': 'test-key',
        'POSTHOG_API_KEY': 'phc_test',
        'POSTHOG_TEAM_ID': '12345'
    }):
        yield


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = MagicMock()
    logger.info = AsyncMock()
    logger.warning = AsyncMock()
    logger.error = AsyncMock()
    logger.debug = AsyncMock()
    return logger
