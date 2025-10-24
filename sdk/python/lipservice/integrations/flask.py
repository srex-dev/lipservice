"""Flask integration for LipService SDK."""

import uuid
from typing import Any

try:
    from flask import Flask, g, request
except ImportError:
    raise ImportError("Flask is not installed. Install with: pip install lipservice-sdk[flask]")

import structlog

from lipservice.config import configure_adaptive_logging

logger = structlog.get_logger(__name__)


def init_lipservice(
    app: Flask,
    service_name: str,
    lipservice_url: str,
    api_key: str | None = None,
) -> None:
    """
    Initialize LipService for Flask applications.

    Example:
        >>> from flask import Flask
        >>> from lipservice.integrations.flask import init_lipservice
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> init_lipservice(
        ...     app,
        ...     service_name="my-flask-app",
        ...     lipservice_url="https://lipservice.company.com"
        ... )
        >>>
        >>> @app.route("/")
        >>> def index():
        ...     logger.info("handling_request")  # Automatically sampled!
        ...     return "Hello"
    """
    # Configure LipService
    configure_adaptive_logging(
        service_name=service_name,
        lipservice_url=lipservice_url,
        api_key=api_key,
    )

    # Add request context
    @app.before_request
    def before_request() -> None:
        """Set up request context."""
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.logger = logger.bind(
            request_id=g.request_id,
            path=request.path,
            method=request.method,
        )

    @app.after_request
    def after_request(response: Any) -> Any:
        """Add request ID to response."""
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        return response

    logger.info("lipservice_flask_initialized", service=service_name)

