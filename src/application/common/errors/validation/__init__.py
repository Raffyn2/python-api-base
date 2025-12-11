"""Validation errors.

Provides validation-related exception types for application layer.

**Feature: python-api-base-2025-state-of-art**

Note: For HTTP/API handlers with RFC 7807 support, use core.errors.ValidationError.
"""

from application.common.errors.validation.validation_error import ValidationError

__all__ = ["ValidationError"]
