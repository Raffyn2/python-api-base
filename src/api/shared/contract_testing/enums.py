"""Contract testing enums.

**Feature: code-review-refactoring, Task 17.1: Refactor contract_testing.py**
**Validates: Requirements 5.4**
"""

from enum import Enum


class ContractStatus(str, Enum):
    """Status of a contract verification."""

    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"


class MatcherType(str, Enum):
    """Types of matchers for contract validation."""

    EXACT = "exact"
    TYPE = "type"
    REGEX = "regex"
    RANGE = "range"
    CONTAINS = "contains"
    ANY = "any"
