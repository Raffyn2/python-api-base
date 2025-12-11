"""Shared error handling utilities for Examples API.

**Feature: example-system-demo**
**Validates: Requirements 2.1**
"""

from typing import Any

import structlog
from fastapi import HTTPException

from application.examples import NotFoundError, ValidationError

logger = structlog.get_logger(__name__)


def handle_result_error(
    error: Any,
    *,
    correlation_id: str | None = None,
) -> HTTPException:
    """Convert use case error to HTTP exception.

    Args:
        error: Error from Result pattern.
        correlation_id: Request correlation ID for tracing.

    Returns:
        HTTPException with appropriate status code.
    """
    log_context = {"correlation_id": correlation_id} if correlation_id else {}

    if isinstance(error, NotFoundError):
        logger.warning(
            "resource_not_found",
            error_type=type(error).__name__,
            **log_context,
        )
        return HTTPException(status_code=404, detail=error.message)

    if isinstance(error, ValidationError):
        logger.warning(
            "validation_error",
            error_type=type(error).__name__,
            **log_context,
        )
        return HTTPException(status_code=422, detail=error.message)

    # Log internal errors but don't expose details to client
    logger.error(
        "internal_error",
        error_type=type(error).__name__,
        **log_context,
    )
    return HTTPException(status_code=500, detail="Internal server error")
