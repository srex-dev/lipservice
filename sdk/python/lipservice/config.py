"""Configuration and setup for LipService SDK."""

import asyncio
import logging
from typing import Any

import structlog

from lipservice.client import LipServiceClient
from lipservice.handler import LipServiceHandler, StructlogProcessor
from lipservice.models import SDKConfig
from lipservice.sampler import AdaptiveSampler

# Global state
_sampler: AdaptiveSampler | None = None
_client: LipServiceClient | None = None
_config: SDKConfig | None = None


def configure_adaptive_logging(
    service_name: str,
    lipservice_url: str,
    api_key: str | None = None,
    policy_refresh_interval: int = 300,
    pattern_report_interval: int = 600,
    downstream_handler: logging.Handler | None = None,
    use_structlog: bool = True,
    # PostHog integration
    posthog_api_key: str | None = None,
    posthog_team_id: str | None = None,
    posthog_endpoint: str = "https://app.posthog.com",
    **kwargs: Any,
) -> None:
    """
    Configure LipService adaptive logging in one line.

    This is the main entry point for the SDK. Call this once at application
    startup to enable intelligent log sampling.

    Args:
        service_name: Service identifier
        lipservice_url: LipService API URL
        api_key: Optional API key for authentication
        policy_refresh_interval: Seconds between policy refreshes (default: 300)
        pattern_report_interval: Seconds between pattern reports (default: 600)
        downstream_handler: Handler to forward sampled logs to (e.g., PostHog handler)
        use_structlog: Whether to configure structlog (default: True)
        posthog_api_key: PostHog API key (phc_xxx) for direct PostHog integration
        posthog_team_id: PostHog team ID for direct PostHog integration
        posthog_endpoint: PostHog endpoint (default: PostHog Cloud)
        **kwargs: Additional configuration options

    Example:
        >>> # Basic configuration
        >>> configure_adaptive_logging(
        ...     service_name="my-api",
        ...     lipservice_url="https://lipservice.company.com"
        ... )

        >>> # With PostHog integration
        >>> configure_adaptive_logging(
        ...     service_name="my-api",
        ...     lipservice_url="https://lipservice.company.com",
        ...     posthog_api_key="phc_xxx",
        ...     posthog_team_id="12345"
        ... )
    """
    global _sampler, _client, _config

    # Create configuration
    _config = SDKConfig(
        service_name=service_name,
        lipservice_url=lipservice_url,
        api_key=api_key,
        policy_refresh_interval=policy_refresh_interval,
        pattern_report_interval=pattern_report_interval,
        **kwargs,
    )

    # Create client
    _client = LipServiceClient(
        base_url=lipservice_url,
        service_name=service_name,
        api_key=api_key,
    )

    # Create sampler
    _sampler = AdaptiveSampler(
        client=_client,
        policy_refresh_interval=policy_refresh_interval,
        pattern_report_interval=pattern_report_interval,
    )

    # Start sampler
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_sampler.start())
    except RuntimeError:
        # No event loop running, start in background thread
        import threading

        def start_sampler() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_sampler.start())
            loop.run_forever()

        thread = threading.Thread(target=start_sampler, daemon=True)
        thread.start()

    # Create PostHog handler if configured
    posthog_handler = None
    if posthog_api_key and posthog_team_id:
        from lipservice.posthog import create_posthog_handler

        posthog_handler = create_posthog_handler(
            api_key=posthog_api_key,
            team_id=posthog_team_id,
            endpoint=posthog_endpoint,
        )
        # logger.info("posthog_handler_created", team_id=posthog_team_id, endpoint=posthog_endpoint)

    # Configure standard logging
    if downstream_handler or posthog_handler or not use_structlog:
        # Use PostHog handler as downstream if available, otherwise use provided handler
        final_downstream_handler = posthog_handler or downstream_handler

        handler = LipServiceHandler(
            sampler=_sampler,
            downstream_handler=final_downstream_handler,
        )
        logging.root.addHandler(handler)

    # Configure structlog
    if use_structlog:
        processor = StructlogProcessor(_sampler)

        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                processor,  # Our sampling processor
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
        )

    # Log configuration
    logger = structlog.get_logger(__name__)
    logger.info(
        "lipservice_configured",
        service=service_name,
        lipservice_url=lipservice_url,
        policy_refresh_interval=policy_refresh_interval,
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a logger instance.

    If structlog is configured, returns a structlog logger.
    Otherwise, returns a standard Python logger.

    Args:
        name: Logger name (module name)

    Returns:
        Logger instance
    """
    try:
        return structlog.get_logger(name)
    except Exception:
        return logging.getLogger(name)


def get_sampler() -> AdaptiveSampler | None:
    """Get the global sampler instance."""
    return _sampler


def get_client() -> LipServiceClient | None:
    """Get the global LipService client instance."""
    return _client


def get_config() -> SDKConfig | None:
    """Get the global SDK configuration."""
    return _config


async def shutdown() -> None:
    """
    Shut down LipService SDK gracefully.

    Call this during application shutdown to ensure final
    pattern statistics are reported.
    """
    global _sampler, _client

    if _sampler:
        await _sampler.stop()
        _sampler = None

    if _client:
        await _client.close()
        _client = None

    logger = structlog.get_logger(__name__)
    logger.info("lipservice_shutdown_complete")

