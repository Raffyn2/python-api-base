"""Fuzzing Integration Module.

**Feature: code-review-refactoring, Task 16.3: Refactor fuzzing.py**
**Validates: Requirements 5.3**
"""

from .config import FuzzingConfig
from .corpus import CorpusManager, CrashManager
from .enums import CrashType, FuzzingStatus
from .fuzzer import Fuzzer, FuzzingResult
from .models import CoverageInfo, CrashInfo, FuzzInput, FuzzingStats
from .mutator import InputMinimizer, InputMutator

__all__ = [
    "CorpusManager",
    "CoverageInfo",
    "CrashInfo",
    "CrashManager",
    "CrashType",
    "FuzzInput",
    "Fuzzer",
    "FuzzingConfig",
    "FuzzingResult",
    "FuzzingStats",
    "FuzzingStatus",
    "InputMinimizer",
    "InputMutator",
]
