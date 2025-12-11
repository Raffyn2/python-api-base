"""CQRS exceptions module.

Provides custom exceptions for CQRS infrastructure.

**Feature: python-api-base-2025-state-of-art**
**Refactored: 2025 - Added EventHandlerError**
"""

from application.common.cqrs.exceptions.exceptions import (
    CQRSError,
    EventHandlerError,
    HandlerAlreadyRegisteredError,
    HandlerNotFoundError,
    MiddlewareError,
)

__all__ = [
    "CQRSError",
    "EventHandlerError",
    "HandlerAlreadyRegisteredError",
    "HandlerNotFoundError",
    "MiddlewareError",
]
