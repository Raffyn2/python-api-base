"""Base error classes for application layer.

Provides fundamental exception types for error handling.

**Feature: python-api-base-2025-state-of-art**

Note: HandlerNotFoundError exists in two places with different hierarchies:
- application.common.errors.base.handler_not_found (ApplicationError hierarchy)
- application.common.cqrs.exceptions (CQRSError hierarchy)
Both are intentional for different use cases.
"""

from application.common.errors.base.application_error import ApplicationError
from application.common.errors.base.handler_not_found import HandlerNotFoundError

__all__ = [
    "ApplicationError",
    "HandlerNotFoundError",
]
