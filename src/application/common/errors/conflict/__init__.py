"""Conflict errors.

Provides conflict exception types for application layer.

**Feature: python-api-base-2025-state-of-art**

Note: For HTTP/API handlers with RFC 7807 support, use core.errors.ConflictError.
"""

from application.common.errors.conflict.conflict_error import ConflictError

__all__ = ["ConflictError"]
