"""Not found errors.

Provides not found exception types for application layer.

**Feature: python-api-base-2025-state-of-art**

Note: For HTTP/API handlers with RFC 7807 support, use core.errors.EntityNotFoundError.
"""

from application.common.errors.not_found.not_found_error import NotFoundError

__all__ = ["NotFoundError"]
