"""Authentication and authorization errors.

Provides auth-related exception types for application layer.

**Feature: python-api-base-2025-state-of-art**

Note: For HTTP/API handlers with RFC 7807 support, use:
- core.errors.AuthenticationError (instead of UnauthorizedError)
- core.errors.AuthorizationError (instead of ForbiddenError)
"""

from application.common.errors.auth.forbidden_error import ForbiddenError
from application.common.errors.auth.unauthorized_error import UnauthorizedError

__all__ = [
    "ForbiddenError",
    "UnauthorizedError",
]
