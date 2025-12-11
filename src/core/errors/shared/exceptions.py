"""Custom exception hierarchy for shared modules.

Re-exports all exception classes for backward compatibility.
Implementation split into focused modules for one-class-per-file compliance.

**Feature: shared-modules-refactoring**
**Validates: Requirements 1.3, 2.4, 10.3**
**Refactored: Split into focused modules for one-class-per-file compliance**
"""

# Re-export all classes for backward compatibility
from core.errors.shared.base import SharedModuleError
from core.errors.shared.phase2_errors import (
    EntityResolutionError,
    FederationValidationError,
    FilterValidationError,
    Phase2ModuleError,
    PoolInvariantViolationError,
    SnapshotIntegrityError,
)
from core.errors.shared.security_errors import (
    AuthenticationError,
    DecryptionError,
    EncryptionError,
    PatternValidationError,
    SecurityModuleError,
)
from core.errors.shared.task_errors import (
    BanOperationError,
    LockAcquisitionTimeoutError,
    RollbackError,
    TaskExecutionError,
)
from core.errors.shared.validation_errors import ValidationError

__all__ = [
    "AuthenticationError",
    "BanOperationError",
    "DecryptionError",
    "EncryptionError",
    "EntityResolutionError",
    "FederationValidationError",
    "FilterValidationError",
    "LockAcquisitionTimeoutError",
    "PatternValidationError",
    # Phase 2
    "Phase2ModuleError",
    "PoolInvariantViolationError",
    "RollbackError",
    # Security
    "SecurityModuleError",
    # Base
    "SharedModuleError",
    "SnapshotIntegrityError",
    # Task errors
    "TaskExecutionError",
    # Validation
    "ValidationError",
]
