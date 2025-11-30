"""Fuzzing enums.

**Feature: code-review-refactoring, Task 16.3: Refactor fuzzing.py**
**Validates: Requirements 5.3**
"""

from enum import Enum


class FuzzingStatus(Enum):
    """Status of a fuzzing run."""

    RUNNING = "running"
    COMPLETED = "completed"
    CRASHED = "crashed"
    TIMEOUT = "timeout"
    STOPPED = "stopped"


class CrashType(Enum):
    """Types of crashes found during fuzzing."""

    ASSERTION = "assertion"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    MEMORY = "memory"
    SEGFAULT = "segfault"
    UNKNOWN = "unknown"
