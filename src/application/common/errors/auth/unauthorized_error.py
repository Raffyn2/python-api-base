"""Authentication required error.

Raised when authentication is required but not provided.

**Feature: python-api-base-2025-state-of-art**

Note: This is a simplified version for application layer use.
For HTTP/API handlers, use core.errors.AuthenticationError which includes
correlation_id, timestamp, and RFC 7807 support.
"""

from application.common.errors.base.application_error import ApplicationError


class UnauthorizedError(ApplicationError):
    """Authentication required error.

    Raised when a request requires authentication but the user
    is not authenticated or the credentials are invalid.

    Example:
        >>> raise UnauthorizedError("Invalid credentials")
    """

    def __init__(self, message: str = "Authentication required") -> None:
        """Initialize unauthorized error.

        Args:
            message: Error message describing the authentication issue.
        """
        super().__init__(message=message, code="UNAUTHORIZED")
