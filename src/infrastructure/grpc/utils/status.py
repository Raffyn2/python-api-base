"""Error to gRPC status code mapping.

This module provides utilities for converting domain exceptions
to appropriate gRPC status codes following best practices.
"""

from __future__ import annotations

import asyncio

from grpc import StatusCode


class ValidationError(Exception):
    """Validation error for invalid input."""


class NotFoundError(Exception):
    """Resource not found error."""


class UnauthorizedError(Exception):
    """Authentication required error."""


class ForbiddenError(Exception):
    """Permission denied error."""


class ConflictError(Exception):
    """Resource conflict error."""


class RateLimitError(Exception):
    """Rate limit exceeded error."""


class ExternalServiceError(Exception):
    """External service unavailable error."""


class DatabaseError(Exception):
    """Database operation error."""


class OperationTimeoutError(Exception):
    """Operation timeout error."""


# Alias for backward compatibility
TimeoutError = OperationTimeoutError


# Mapping of domain exceptions to gRPC status codes
ERROR_STATUS_MAP: dict[type[Exception], StatusCode] = {
    ValidationError: StatusCode.INVALID_ARGUMENT,
    NotFoundError: StatusCode.NOT_FOUND,
    UnauthorizedError: StatusCode.UNAUTHENTICATED,
    ForbiddenError: StatusCode.PERMISSION_DENIED,
    ConflictError: StatusCode.ALREADY_EXISTS,
    RateLimitError: StatusCode.RESOURCE_EXHAUSTED,
    ExternalServiceError: StatusCode.UNAVAILABLE,
    DatabaseError: StatusCode.INTERNAL,
    OperationTimeoutError: StatusCode.DEADLINE_EXCEEDED,
    ValueError: StatusCode.INVALID_ARGUMENT,
    KeyError: StatusCode.NOT_FOUND,
    PermissionError: StatusCode.PERMISSION_DENIED,
    ConnectionError: StatusCode.UNAVAILABLE,
    asyncio.TimeoutError: StatusCode.DEADLINE_EXCEEDED,
    TimeoutError: StatusCode.DEADLINE_EXCEEDED,
}


def get_status_code(exc: Exception) -> StatusCode:
    """Get gRPC status code for an exception.

    Args:
        exc: The exception to map

    Returns:
        The corresponding gRPC StatusCode
    """
    exc_type = type(exc)

    # Direct match
    if exc_type in ERROR_STATUS_MAP:
        return ERROR_STATUS_MAP[exc_type]

    # Check inheritance chain
    for error_type, status_code in ERROR_STATUS_MAP.items():
        if isinstance(exc, error_type):
            return status_code

    # Default to INTERNAL for unknown errors
    return StatusCode.INTERNAL


def exception_to_status(exc: Exception) -> tuple[StatusCode, str]:
    """Convert exception to gRPC status code and message.

    Args:
        exc: The exception to convert

    Returns:
        Tuple of (StatusCode, error message)
    """
    status_code = get_status_code(exc)
    message = str(exc) if str(exc) else exc.__class__.__name__

    return status_code, message


def status_to_exception(status_code: StatusCode, message: str) -> Exception:
    """Convert gRPC status code to domain exception.

    Args:
        status_code: The gRPC status code
        message: The error message

    Returns:
        The corresponding domain exception
    """
    # Reverse mapping
    status_to_error: dict[StatusCode, type[Exception]] = {
        StatusCode.INVALID_ARGUMENT: ValidationError,
        StatusCode.NOT_FOUND: NotFoundError,
        StatusCode.UNAUTHENTICATED: UnauthorizedError,
        StatusCode.PERMISSION_DENIED: ForbiddenError,
        StatusCode.ALREADY_EXISTS: ConflictError,
        StatusCode.RESOURCE_EXHAUSTED: RateLimitError,
        StatusCode.UNAVAILABLE: ExternalServiceError,
        StatusCode.INTERNAL: DatabaseError,
        StatusCode.DEADLINE_EXCEEDED: OperationTimeoutError,
    }

    error_class = status_to_error.get(status_code, Exception)
    return error_class(message)


def is_retryable_status(status_code: StatusCode) -> bool:
    """Check if a status code indicates a retryable error.

    Args:
        status_code: The gRPC status code

    Returns:
        True if the error is retryable
    """
    retryable_codes = {
        StatusCode.UNAVAILABLE,
        StatusCode.RESOURCE_EXHAUSTED,
        StatusCode.ABORTED,
        StatusCode.DEADLINE_EXCEEDED,
    }
    return status_code in retryable_codes


def is_client_error(status_code: StatusCode) -> bool:
    """Check if a status code indicates a client error.

    Args:
        status_code: The gRPC status code

    Returns:
        True if the error is a client error
    """
    client_error_codes = {
        StatusCode.INVALID_ARGUMENT,
        StatusCode.NOT_FOUND,
        StatusCode.ALREADY_EXISTS,
        StatusCode.PERMISSION_DENIED,
        StatusCode.UNAUTHENTICATED,
        StatusCode.FAILED_PRECONDITION,
        StatusCode.OUT_OF_RANGE,
    }
    return status_code in client_error_codes
