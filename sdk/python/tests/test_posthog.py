"""
Tests for PostHog OTLP integration.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest

from lipservice.posthog import (
    PostHogConfig,
    PostHogHandler,
    PostHogOTLPExporter,
    create_posthog_handler,
)


class TestPostHogConfig:
    """Test PostHog configuration."""

    def test_config_creation(self):
        """Test PostHog configuration creation."""
        config = PostHogConfig(
            api_key="phc_test",
            team_id="12345",
            endpoint="https://app.posthog.com",
            timeout=15.0,
            batch_size=50,
            flush_interval=3.0,
            max_retries=5,
        )

        assert config.api_key == "phc_test"
        assert config.team_id == "12345"
        assert config.endpoint == "https://app.posthog.com"
        assert config.timeout == 15.0
        assert config.batch_size == 50
        assert config.flush_interval == 3.0
        assert config.max_retries == 5
        assert config.otlp_endpoint == "https://app.posthog.com/api/v1/otlp/v1/logs"

    def test_config_defaults(self):
        """Test PostHog configuration defaults."""
        config = PostHogConfig(api_key="phc_test", team_id="12345")

        assert config.endpoint == "https://app.posthog.com"
        assert config.timeout == 10.0
        assert config.batch_size == 100
        assert config.flush_interval == 5.0
        assert config.max_retries == 3

    def test_get_headers(self):
        """Test header generation."""
        config = PostHogConfig(api_key="phc_test", team_id="12345")
        headers = config.get_headers()

        assert headers["Content-Type"] == "application/x-protobuf"
        assert headers["Authorization"] == "Bearer phc_test"
        assert headers["X-PostHog-Team-Id"] == "12345"


class TestPostHogOTLPExporter:
    """Test PostHog OTLP exporter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PostHogConfig(
            api_key="phc_test",
            team_id="12345",
            batch_size=2,  # Small batch for testing
            flush_interval=0.1,  # Fast flush for testing
        )

    @pytest.fixture
    def exporter(self, config):
        """Create test exporter."""
        return PostHogOTLPExporter(config)

    def test_exporter_creation(self, exporter, config):
        """Test exporter creation."""
        assert exporter.config == config
        assert exporter.batch == []
        assert not exporter._running

    def test_severity_number_mapping(self, exporter):
        """Test severity number mapping."""
        assert exporter._get_severity_number("TRACE") == 1
        assert exporter._get_severity_number("DEBUG") == 5
        assert exporter._get_severity_number("INFO") == 9
        assert exporter._get_severity_number("WARN") == 13
        assert exporter._get_severity_number("WARNING") == 13
        assert exporter._get_severity_number("ERROR") == 17
        assert exporter._get_severity_number("FATAL") == 21
        assert exporter._get_severity_number("CRITICAL") == 21
        assert exporter._get_severity_number("UNKNOWN") == 9  # Default

    def test_create_log_record(self, exporter):
        """Test log record creation."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)

        log_record = exporter._create_log_record(
            message="Test message",
            severity="INFO",
            timestamp=timestamp,
            context=None,
            user_id="123",
            request_id="req-456",
        )

        assert log_record.severity_text == "INFO"
        assert log_record.severity_number == 9
        assert log_record.body.string_value == "Test message"

        # Check attributes
        attributes = {attr.key: attr.value for attr in log_record.attributes}
        assert attributes["severity_text"].string_value == "INFO"
        assert attributes["severity_number"].int_value == 9
        assert attributes["user_id"].string_value == "123"
        assert attributes["request_id"].string_value == "req-456"

    def test_create_log_record_with_context(self, exporter):
        """Test log record creation with context."""
        from lipservice.models import LogContext

        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        context = LogContext(
            user_id="123",
            request_id="req-456",
            trace_id="trace-789",
            span_id="span-101",
            custom_fields={"environment": "test"},
        )

        log_record = exporter._create_log_record(
            message="Test message",
            severity="ERROR",
            timestamp=timestamp,
            context=context,
        )

        attributes = {attr.key: attr.value for attr in log_record.attributes}
        assert attributes["context.user_id"].string_value == "123"
        assert attributes["context.request_id"].string_value == "req-456"
        assert attributes["context.trace_id"].string_value == "trace-789"
        assert attributes["context.span_id"].string_value == "span-101"
        assert attributes["context.environment"].string_value == "test"

    @pytest.mark.asyncio
    async def test_start_stop(self, exporter):
        """Test exporter start and stop."""
        # Mock the client
        exporter.client = AsyncMock()

        # Start exporter
        await exporter.start()
        assert exporter._running
        assert exporter._flush_task is not None

        # Stop exporter
        await exporter.stop()
        assert not exporter._running
        exporter.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_log(self, exporter):
        """Test log export."""
        # Mock the client
        exporter.client = AsyncMock()

        # Start exporter
        await exporter.start()

        # Export a log
        timestamp = datetime.now()
        await exporter.export_log(
            message="Test message",
            severity="INFO",
            timestamp=timestamp,
        )

        # Check batch
        assert len(exporter.batch) == 1
        assert exporter.batch[0].body.string_value == "Test message"
        assert exporter.batch[0].severity_text == "INFO"

        await exporter.stop()

    @pytest.mark.asyncio
    async def test_batch_flush(self, exporter):
        """Test batch flushing."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        exporter.client = AsyncMock()
        exporter.client.post.return_value = mock_response

        # Start exporter
        await exporter.start()

        # Add logs to batch
        timestamp = datetime.now()
        await exporter.export_log("Message 1", "INFO", timestamp)
        await exporter.export_log("Message 2", "WARNING", timestamp)

        # Batch should be full (size=2)
        assert len(exporter.batch) == 2

        # Manually flush
        await exporter._flush_batch()

        # Batch should be empty
        assert len(exporter.batch) == 0

        # Check that POST was called
        exporter.client.post.assert_called_once()
        call_args = exporter.client.post.call_args
        assert call_args[0][0] == exporter.config.otlp_endpoint

        await exporter.stop()

    @pytest.mark.asyncio
    async def test_flush_with_retries(self, exporter):
        """Test flush with retries."""
        # Mock retryable error then success
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429  # Rate limited

        mock_success_response = MagicMock()
        mock_success_response.raise_for_status.return_value = None

        exporter.client = AsyncMock()
        exporter.client.post.side_effect = [
            httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_error_response),
            mock_success_response,
        ]

        # Start exporter
        await exporter.start()

        # Add log to batch
        timestamp = datetime.now()
        await exporter.export_log("Test message", "INFO", timestamp)

        # Flush with retries
        await exporter._flush_batch()

        # Should have retried once
        assert exporter.client.post.call_count == 2

        await exporter.stop()

    @pytest.mark.asyncio
    async def test_flush_max_retries(self, exporter):
        """Test flush with max retries exceeded."""
        # Mock persistent error
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429  # Rate limited

        exporter.client = AsyncMock()
        exporter.client.post.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=MagicMock(),
            response=mock_error_response
        )

        # Start exporter
        await exporter.start()

        # Add log to batch
        timestamp = datetime.now()
        await exporter.export_log("Test message", "INFO", timestamp)

        # Flush with retries
        await exporter._flush_batch()

        # Should have retried max times
        assert exporter.client.post.call_count == exporter.config.max_retries + 1

        await exporter.stop()


class TestPostHogHandler:
    """Test PostHog logging handler."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PostHogConfig(api_key="phc_test", team_id="12345")

    @pytest.fixture
    def handler(self, config):
        """Create test handler."""
        return PostHogHandler(config)

    def test_handler_creation(self, handler, config):
        """Test handler creation."""
        assert handler.config == config
        assert isinstance(handler.exporter, PostHogOTLPExporter)
        assert not handler._started

    @patch('asyncio.create_task')
    def test_emit_log_record(self, mock_create_task, handler):
        """Test emitting log record."""
        # Create a mock log record
        record = MagicMock()
        record.getMessage.return_value = "Test message"
        record.levelname = "INFO"
        record.created = 1640995200.0  # 2022-01-01 00:00:00
        record.name = "test.logger"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42

        # Mock the exporter
        handler.exporter.export_log = AsyncMock()

        # Emit the record
        handler.emit(record)

        # Check that exporter.export_log was called
        mock_create_task.assert_called_once()

        # Get the coroutine that was passed to create_task
        coroutine = mock_create_task.call_args[0][0]

        # Check the coroutine arguments
        assert coroutine.cr_frame.f_locals['message'] == "Test message"
        assert coroutine.cr_frame.f_locals['severity'] == "INFO"
        assert coroutine.cr_frame.f_locals['attributes']['logger_name'] == "test.logger"

    @patch('asyncio.create_task')
    def test_emit_with_lipservice_attributes(self, mock_create_task, handler):
        """Test emitting log record with LipService attributes."""
        # Create a mock log record with LipService attributes
        record = MagicMock()
        record.getMessage.return_value = "Test message"
        record.levelname = "ERROR"
        record.created = 1640995200.0
        record.name = "test.logger"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.lipservice_signature = "test_signature"
        record.lipservice_sampled = True

        # Mock the exporter
        handler.exporter.export_log = AsyncMock()

        # Emit the record
        handler.emit(record)

        # Check that exporter.export_log was called
        mock_create_task.assert_called_once()

        # Get the coroutine that was passed to create_task
        coroutine = mock_create_task.call_args[0][0]

        # Check the coroutine arguments
        attributes = coroutine.cr_frame.f_locals['attributes']
        assert attributes['lipservice_signature'] == "test_signature"
        assert attributes['lipservice_sampled'] is True

    @patch('asyncio.run')
    def test_close_handler(self, mock_run, handler):
        """Test closing handler."""
        handler._started = True

        # Close handler
        handler.close()

        # Check that exporter.stop was called
        mock_run.assert_called_once()


class TestCreatePostHogHandler:
    """Test create_posthog_handler function."""

    def test_create_handler(self):
        """Test creating PostHog handler."""
        handler = create_posthog_handler(
            api_key="phc_test",
            team_id="12345",
            endpoint="https://app.posthog.com",
            timeout=15.0,
            batch_size=50,
        )

        assert isinstance(handler, PostHogHandler)
        assert handler.config.api_key == "phc_test"
        assert handler.config.team_id == "12345"
        assert handler.config.endpoint == "https://app.posthog.com"
        assert handler.config.timeout == 15.0
        assert handler.config.batch_size == 50

    def test_create_handler_defaults(self):
        """Test creating PostHog handler with defaults."""
        handler = create_posthog_handler(
            api_key="phc_test",
            team_id="12345",
        )

        assert isinstance(handler, PostHogHandler)
        assert handler.config.api_key == "phc_test"
        assert handler.config.team_id == "12345"
        assert handler.config.endpoint == "https://app.posthog.com"
        assert handler.config.timeout == 10.0
        assert handler.config.batch_size == 100


class TestOTLPRequestCreation:
    """Test OTLP request creation."""

    def test_create_otlp_request(self):
        """Test OTLP request creation."""
        config = PostHogConfig(api_key="phc_test", team_id="12345")
        exporter = PostHogOTLPExporter(config)

        # Add some log records to batch
        timestamp = datetime.now()
        exporter.batch.append(exporter._create_log_record("Message 1", "INFO", timestamp))
        exporter.batch.append(exporter._create_log_record("Message 2", "ERROR", timestamp))

        # Create OTLP request
        request = exporter._create_otlp_request()

        assert isinstance(request, ExportLogsServiceRequest)
        assert len(request.resource_logs) == 1

        resource_logs = request.resource_logs[0]
        assert len(resource_logs.scope_logs) == 1

        scope_logs = resource_logs.scope_logs[0]
        assert len(scope_logs.log_records) == 2

        # Check resource attributes
        resource_attrs = {attr.key: attr.value for attr in resource_logs.resource.attributes}
        assert resource_attrs["service.name"].string_value == "lipservice-sdk"
        assert resource_attrs["service.version"].string_value == "0.2.0"

        # Check scope attributes
        scope = resource_logs.scope_logs[0].scope
        assert scope.name == "lipservice"
        assert scope.version == "0.2.0"


@pytest.mark.asyncio
async def test_integration_example():
    """Test integration example."""
    # This test simulates the full integration flow
    config = PostHogConfig(
        api_key="phc_test",
        team_id="12345",
        batch_size=1,  # Small batch for testing
    )

    exporter = PostHogOTLPExporter(config)

    # Mock successful HTTP response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    exporter.client = AsyncMock()
    exporter.client.post.return_value = mock_response

    # Start exporter
    await exporter.start()

    # Export logs
    timestamp = datetime.now()
    await exporter.export_log("User login", "INFO", timestamp, user_id="123")
    await exporter.export_log("Payment failed", "ERROR", timestamp, user_id="123", amount=99.99)

    # Wait for flush
    await asyncio.sleep(0.2)

    # Stop exporter
    await exporter.stop()

    # Verify logs were sent
    assert exporter.client.post.call_count >= 1
