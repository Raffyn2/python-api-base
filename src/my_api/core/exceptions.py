"""Application exception hierarchy."""

from typing import Any


class AppException(Exception):
    """Base application exception.

    All application-specific exceptions should inherit from this class.
    Provides structured error information for consistent error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize application exception.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            status_code: HTTP status code.
            details: Additional error details.
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns:
            dict: Exception data as dictionary.
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": self.details,
        }


class EntityNotFoundError(AppException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str | int) -> None:
        """Initialize entity not found error.

        Args:
            entity_type: Type/name of the entity.
            entity_id: ID of the entity that was not found.
        """
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            error_code="ENTITY_NOT_FOUND",
            status_code=404,
            details={"entity_type": entity_type, "entity_id": str(entity_id)},
        )


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(
        self,
        errors: list[dict[str, Any]],
        message: str = "Validation failed",
    ) -> None:
        """Initialize validation error.

        Args:
            errors: List of validation errors with field details.
            message: Overall error message.
        """
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors},
        )


class BusinessRuleViolationError(AppException):
    """Raised when a business rule is violated."""

    def __init__(self, rule: str, message: str) -> None:
        """Initialize business rule violation error.

        Args:
            rule: Name/identifier of the violated rule.
            message: Description of the violation.
        """
        super().__init__(
            message=message,
            error_code=f"BUSINESS_RULE_{rule.upper()}",
            status_code=400,
            details={"rule": rule},
        )


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        scheme: str = "Bearer",
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Error message.
            scheme: Authentication scheme for WWW-Authenticate header.
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details={"scheme": scheme},
        )


class AuthorizationError(AppException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: str | None = None,
    ) -> None:
        """Initialize authorization error.

        Args:
            message: Error message.
            required_permission: The permission that was required.
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
        )


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        retry_after: int,
        message: str = "Rate limit exceeded",
    ) -> None:
        """Initialize rate limit exceeded error.

        Args:
            retry_after: Seconds until the client can retry.
            message: Error message.
        """
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )


class ConflictError(AppException):
    """Raised when there is a resource conflict."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        """Initialize conflict error.

        Args:
            message: Error message.
            resource_type: Type of the conflicting resource.
            resource_id: ID of the conflicting resource.
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )
