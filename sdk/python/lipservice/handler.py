"""Python logging handler with intelligent sampling."""

import asyncio
import logging
from typing import Any

import structlog

from lipservice.sampler import AdaptiveSampler

logger = structlog.get_logger(__name__)


class LipServiceHandler(logging.Handler):
    """
    Custom logging handler that applies intelligent sampling.

    Integrates with Python's standard logging module and forwards
    sampled logs to a downstream handler (e.g., to PostHog).
    """

    def __init__(
        self,
        sampler: AdaptiveSampler,
        downstream_handler: logging.Handler | None = None,
        level: int = logging.NOTSET,
    ):
        """
        Initialize LipService handler.

        Args:
            sampler: AdaptiveSampler for sampling decisions
            downstream_handler: Handler to forward sampled logs to
            level: Logging level
        """
        super().__init__(level)
        self.sampler = sampler
        self.downstream_handler = downstream_handler

        # Ensure sampler is started
        if not self.sampler._running:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.sampler.start())
            except RuntimeError:
                # No event loop running, start in new loop
                asyncio.run(self.sampler.start())

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process log record with intelligent sampling.

        Args:
            record: LogRecord to process
        """
        try:
            # Extract message
            message = self.format(record) if not record.getMessage() else record.getMessage()

            # Extract severity
            severity = record.levelname

            # Make sampling decision
            should_sample, signature = self.sampler.should_sample(
                message=message,
                severity=severity,
            )

            # Add signature to record for downstream handlers
            record.lipservice_signature = signature  # type: ignore
            record.lipservice_sampled = should_sample  # type: ignore

            # Forward to downstream handler if sampled
            if should_sample and self.downstream_handler:
                self.downstream_handler.emit(record)

        except Exception as e:
            self.handleError(record)
            logger.error("handler_emit_error", error=str(e))

    def close(self) -> None:
        """Clean up handler resources."""
        try:
            # Stop sampler
            asyncio.run(self.sampler.stop())
        except Exception as e:
            logger.error("handler_close_error", error=str(e))

        # Close downstream handler
        if self.downstream_handler:
            self.downstream_handler.close()

        super().close()


class StructlogProcessor:
    """
    Structlog processor that applies intelligent sampling.

    Use this with structlog instead of the standard logging handler.
    """

    def __init__(self, sampler: AdaptiveSampler):
        """
        Initialize structlog processor.

        Args:
            sampler: AdaptiveSampler for sampling decisions
        """
        self.sampler = sampler

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Process structlog event with sampling.

        Args:
            logger: Logger instance
            method_name: Log method name
            event_dict: Event dictionary

        Returns:
            Modified event dictionary or raises DropEvent to skip
        """
        # Extract message and severity
        message = event_dict.get("event", "")
        severity = method_name.upper()

        # Make sampling decision
        should_sample, signature = self.sampler.should_sample(
            message=message,
            severity=severity,
        )

        # Add metadata
        event_dict["lipservice_signature"] = signature
        event_dict["lipservice_sampled"] = should_sample

        # Drop event if not sampled
        if not should_sample:
            from structlog import DropEvent

            raise DropEvent

        return event_dict

