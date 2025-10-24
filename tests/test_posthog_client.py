from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.integrations.posthog_client import PostHogLogsClient


@pytest.fixture
def mock_clickhouse_client():
    """Mock ClickHouse client for testing."""
    client = MagicMock()
    return client


@pytest.mark.asyncio
async def test_fetch_logs_from_clickhouse(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [
        ("User logged in", "INFO", datetime.now(), "api"),
        ("Payment processed", "INFO", datetime.now(), "api"),
        ("Error occurred", "ERROR", datetime.now(), "api"),
    ]

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    logs = await posthog_client.fetch_logs(team_id=123, service_name="api", hours=1, limit=1000)

    assert len(logs) == 3
    assert logs[0].message == "User logged in"
    assert logs[0].severity == "INFO"
    assert logs[2].severity == "ERROR"


@pytest.mark.asyncio
async def test_fetch_logs_builds_correct_query(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = []

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    await posthog_client.fetch_logs(team_id=123, service_name="test-api", hours=2, limit=500)

    executed_query = mock_clickhouse_client.execute.call_args[0][0]

    assert "team_id = 123" in executed_query
    assert "service_name = 'test-api'" in executed_query
    assert "INTERVAL 2 HOUR" in executed_query
    assert "LIMIT 500" in executed_query


@pytest.mark.asyncio
async def test_fetch_logs_without_service_filter(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = []

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    await posthog_client.fetch_logs(team_id=123, service_name=None, hours=1)

    executed_query = mock_clickhouse_client.execute.call_args[0][0]

    assert "service_name" not in executed_query


@pytest.mark.asyncio
async def test_fetch_logs_requires_credentials():
    posthog_client = PostHogLogsClient()

    with pytest.raises(ValueError, match="credentials required"):
        await posthog_client.fetch_logs(team_id=123)


def test_get_log_volume(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [(10000,)]

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    volume = posthog_client.get_log_volume(team_id=123, service_name="api", hours=24)

    assert volume == 10000


def test_get_log_volume_with_zero_results(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = []

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    volume = posthog_client.get_log_volume(team_id=123, service_name="api")

    assert volume == 0


def test_get_active_services(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [("api",), ("worker",), ("scheduler",)]

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    services = posthog_client.get_active_services(team_id=123, hours=24)

    assert len(services) == 3
    assert "api" in services
    assert "worker" in services


def test_get_active_services_filters_null_values(mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [("api",), (None,), ("worker",), ("",)]

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    services = posthog_client.get_active_services(team_id=123)

    assert len(services) == 2
    assert "api" in services
    assert "worker" in services


@pytest.mark.parametrize(
    "team_id,hours,expected_in_query",
    [
        (123, 1, "team_id = 123"),
        (456, 24, "INTERVAL 24 HOUR"),
        (789, 48, "team_id = 789"),
    ],
)
def test_query_construction(mock_clickhouse_client, team_id, hours, expected_in_query):
    mock_clickhouse_client.execute.return_value = []

    posthog_client = PostHogLogsClient(clickhouse_host="localhost")
    posthog_client.clickhouse_client = mock_clickhouse_client

    posthog_client.get_log_volume(team_id=team_id, service_name="test", hours=hours)

    executed_query = mock_clickhouse_client.execute.call_args[0][0]
    assert expected_in_query in executed_query

