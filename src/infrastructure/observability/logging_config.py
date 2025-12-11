"""Structured JSON logging configuration.

.. deprecated:: 2025.1
    This module is deprecated. Use one of the following instead:
    - `core.config.observability.logging.configure_logging` for structlog setup
    - `core.shared.logging.config.configure_logging` for ECS-compatible logging

This module will be removed in a future version.
"""

import json
import logging
import sys
import warnings
from datetime import UTC, datetime

warnings.warn(
    "infrastructure.observability.logging_config is deprecated. "
    "Use core.config.observability.logging or core.shared.logging.config instead.",
    DeprecationWarning,
    stacklevel=2,
)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging output."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure root logger with JSON or standard formatting."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JSONFormatter() if json_format else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root.handlers = [handler]
