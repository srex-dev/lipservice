"""
LipService SDK - AI-powered intelligent log sampling

Reduce logging costs by 50-80% while maintaining full observability.

Example:
    >>> from lipservice import configure_adaptive_logging
    >>> configure_adaptive_logging(
    ...     service_name="my-api",
    ...     lipservice_url="https://lipservice.company.com"
    ... )
"""

from lipservice.client import LipServiceClient
from lipservice.config import configure_adaptive_logging, get_logger
from lipservice.handler import LipServiceHandler
from lipservice.posthog import PostHogConfig, PostHogHandler, PostHogOTLPExporter, create_posthog_handler
from lipservice.sampler import AdaptiveSampler

__version__ = "0.2.0"

__all__ = [
    "configure_adaptive_logging",
    "get_logger",
    "LipServiceClient",
    "LipServiceHandler",
    "AdaptiveSampler",
    "PostHogConfig",
    "PostHogHandler", 
    "PostHogOTLPExporter",
    "create_posthog_handler",
]

