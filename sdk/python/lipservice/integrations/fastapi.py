"""FastAPI integration for LipService SDK."""

import uuid
from typing import Callable

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    raise ImportError("FastAPI is not installed. Install with: pip install lipservice-sdk[fastapi]")

import structlog

from lipservice.config import configure_adaptive_logging

logger = structlog.get_logger(__name__)


class LipServiceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for LipService integration.

    Automatically adds request context to all logs within a request.

    Example:
        >>> from fastapi import FastAPI
        >>> from lipservice.integrations.fastapi import LipServiceMiddleware
        >>>
        >>> app = FastAPI()
        >>> app.add_middleware(LipServiceMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with context."""
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind context to all logs in this request
        logger_bound = logger.bind(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )

        # Store in request state
        request.state.logger = logger_bound
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        return response


def configure_lipservice_fastapi(
    service_name: str,
    lipservice_url: str,
    api_key: str | None = None,
) -> None:
    """
    Configure LipService for FastAPI applications.

    Example:
        >>> from fastapi import FastAPI
        >>> from lipservice.integrations.fastapi import (
        ...     configure_lipservice_fastapi,
        ...     LipServiceMiddleware
        ... )
        >>>
        >>> app = FastAPI()
        >>>
        >>> # Configure LipService
        >>> configure_lipservice_fastapi(
        ...     service_name="my-fastapi-app",
        ...     lipservice_url="https://lipservice.company.com"
        ... )
        >>>
        >>> # Add middleware
        >>> app.add_middleware(LipServiceMiddleware)
        >>>
        >>> @app.get("/")
        >>> async def root():
        ...     logger.info("handling_request")  # Automatically sampled!
        ...     return {"message": "Hello"}
    """
    configure_adaptive_logging(
        service_name=service_name,
        lipservice_url=lipservice_url,
        api_key=api_key,
    )

