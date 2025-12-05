"""Security module exceptions.

**Feature: shared-modules-security-fixes**
**Validates: Requirements 1.3, 4.3**
**Refactored: Split from exceptions.py for one-class-per-file compliance**
"""

from __future__ import annotations

from core.errors.shared.base import SharedModuleError


class SecurityModuleError(SharedModuleError):
    """Base exception for security module errors."""


class EncryptionError(SecurityModuleError):
    """Base encryption error with context.

    Raised when encryption operations fail.

    Attributes:
        context: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        context: dict[str, object] | None = None,
    ) -> None:
        """Initialize encryption error.

        Args:
            message: Human-readable error message.
            context: Additional context about the error.
        """
        self.context = context or {}
        super().__init__(message)


class DecryptionError(EncryptionError):
    """Decryption failed.

    Raised when decryption fails due to invalid key, corrupted data,
    or authentication failure.
    """


class AuthenticationError(DecryptionError):
    """Authentication tag verification failed.

    Raised when the GCM authentication tag doesn't match,
    indicating potential data tampering.
    """


class PatternValidationError(SecurityModuleError):
    """Invalid regex pattern.

    Raised when pattern validation fails due to dangerous patterns
    or invalid syntax.

    Attributes:
        pattern: The invalid pattern.
        reason: Reason for the validation failure.
    """

    def __init__(self, pattern: str, reason: str) -> None:
        """Initialize pattern validation error.

        Args:
            pattern: The invalid pattern.
            reason: Reason for the validation failure.
        """
        self.pattern = pattern
        self.reason = reason
        super().__init__(f"Invalid pattern '{pattern}': {reason}")
