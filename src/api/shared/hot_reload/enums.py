"""Hot reload enums for strategies and change types.

**Feature: file-size-compliance-phase2, Task 2.2**
**Validates: Requirements 1.2, 5.1, 5.2, 5.3**
"""

from enum import Enum


class ReloadStrategy(str, Enum):
    """Strategy for reloading modules."""

    FULL = "full"
    CHANGED = "changed"
    DEPENDENCY = "dependency"


class FileChangeType(str, Enum):
    """Type of file change detected."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
