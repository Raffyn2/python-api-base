"""Global exception handlers for FastAPI.

Provides RFC 7807 Problem Details responses for all exception types.
All errors are sanitized to prevent internal detail exposure.

**Feature: api-base-improvements**
**Validates: Requirements 9.1, 9.2**
"""

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from application.common.dto import ProblemDetail
from core.errors.base.domain_errors import (
    AppError,
    AuthenticationError,
    RateLimitExceededError,
)

logger = structlog.get_logger(__name__)


def create_problem_detail(
    request: Request,
    status: int,
    title: str,
    error_code: str,
    detail: str | None = None,
    errors: list[dict] | None = None,
) -> dict[str, Any]:
    """Create RFC 7807 Problem Details response."""
    return ProblemDetail(
        type=f"https://api.example.com/errors/{error_code}",
        title=title,
        status=status,
        detail=detail,
        instance=str(request.url),
        errors=errors,
    ).model_dump(mode="json")


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application exceptions."""
    correlation_id = _get_correlation_id(request)

    logger.warning(
        "app_exception",
        correlation_id=correlation_id,
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=str(request.url.path),
    )

    content = create_problem_detail(
        request=request,
        status=exc.status_code,
        title=exc.error_code.replace("_", " ").title(),
        error_code=exc.error_code,
        detail=exc.message,
        errors=exc.details.get("errors") if exc.details else None,
    )

    headers = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = exc.details.get("scheme", "Bearer")
    elif isinstance(exc, RateLimitExceededError):
        headers["Retry-After"] = str(exc.details.get("retry_after", 60))

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers if headers else None,
    )


async def validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    correlation_id = _get_correlation_id(request)

    errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "code": error["type"],
        }
        for error in exc.errors()
    ]

    logger.info(
        "validation_error",
        correlation_id=correlation_id,
        path=str(request.url.path),
        error_count=len(errors),
    )

    content = create_problem_detail(
        request=request,
        status=422,
        title="Validation Error",
        error_code="VALIDATION_ERROR",
        detail="Request validation failed",
        errors=errors,
    )

    return JSONResponse(status_code=422, content=content)


def _get_correlation_id(request: Request) -> str | None:
    """Extract correlation ID from request state or headers."""
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors without exposing internals."""
    correlation_id = _get_correlation_id(request)

    # Log the full error for debugging (structlog handles exc_info automatically)
    logger.exception(
        "unhandled_exception",
        correlation_id=correlation_id,
        request_url=str(request.url),
        method=request.method,
        error_type=type(exc).__name__,
    )

    # Return generic error without internal details
    content = create_problem_detail(
        request=request,
        status=500,
        title="Internal Server Error",
        error_code="INTERNAL_ERROR",
        detail="An unexpected error occurred. Please try again later.",
    )

    return JSONResponse(status_code=500, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
