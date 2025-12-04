"""Idempotency support for API operations.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 23.1, 23.2, 23.3, 23.4, 23.5, 23.6**

Provides:
- IdempotencyHandler: Core idempotency logic with Redis storage
- IdempotencyMiddleware: FastAPI middleware for automatic handling
- IdempotencyKeyConflictError: Error for key reuse with different body
"""

from .errors import IdempotencyKeyConflictError, IdempotencyKeyMissingError
from .handler import (
    IdempotencyConfig,
    IdempotencyHandler,
    IdempotencyRecord,
)
from .middleware import IdempotencyMiddleware

__all__ = [
    "IdempotencyConfig",
    "IdempotencyHandler",
    "IdempotencyKeyConflictError",
    "IdempotencyKeyMissingError",
    "IdempotencyMiddleware",
    "IdempotencyRecord",
]
