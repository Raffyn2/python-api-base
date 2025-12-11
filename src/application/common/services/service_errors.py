"""Service-specific error types.

**Feature: python-api-base-2025-validation**
**Validates: Requirements 22.1, 22.2, 22.3, 22.4**

Service layer errors that inherit from ApplicationError.
These are distinct from:
- application.common.errors: Simple errors for general application use
- core.errors: Full RFC 7807 errors for HTTP handlers
- interface.errors: HTTP-specific errors with status codes

The service layer errors are designed for Result pattern usage within services.
"""

from __future__ import annotations

from typing import Any

from application.common.errors import ApplicationError


class ServiceError(ApplicationError):
    """Base error for service operations.

    Inherits from ApplicationError for consistent error handling.
    """

    def __init__(
        self,
        message: str,
        code: str = "SERVICE_ERROR",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details)


class NotFoundError(ServiceError):
    """Entity not found error."""

    status_code: int = 404

    def __init__(self, entity_type: str, entity_id: Any) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            code="NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": str(entity_id)},
        )


class ValidationError(ServiceError):
    """Validation error for service operations."""

    status_code: int = 400

    def __init__(
        self,
        message: str,
        field: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.field = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )


class ConflictError(ServiceError):
    """Conflict error (e.g., duplicate entry)."""

    status_code: int = 409

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="CONFLICT", details=details)


class DeleteError(ServiceError):
    """Error during delete operation."""

    status_code: int = 400

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DELETE_ERROR", details=details)
