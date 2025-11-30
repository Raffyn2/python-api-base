"""Contract matchers.

**Feature: code-review-refactoring, Task 17.1: Refactor contract_testing.py**
**Validates: Requirements 5.4**
"""

import re
from dataclasses import dataclass
from typing import Any

from .enums import MatcherType


@dataclass
class Matcher:
    """A matcher for validating values in contracts."""

    matcher_type: MatcherType
    expected: Any = None
    min_value: Any = None
    max_value: Any = None
    pattern: str | None = None

    def matches(self, actual: Any) -> bool:
        """Check if actual value matches the expectation."""
        if self.matcher_type == MatcherType.EXACT:
            return actual == self.expected
        elif self.matcher_type == MatcherType.TYPE:
            return isinstance(actual, self.expected)
        elif self.matcher_type == MatcherType.REGEX:
            if self.pattern and isinstance(actual, str):
                return bool(re.match(self.pattern, actual))
            return False
        elif self.matcher_type == MatcherType.RANGE:
            if self.min_value is not None and actual < self.min_value:
                return False
            if self.max_value is not None and actual > self.max_value:
                return False
            return True
        elif self.matcher_type == MatcherType.CONTAINS:
            if isinstance(actual, (str, list, dict)):
                return self.expected in actual
            return False
        elif self.matcher_type == MatcherType.ANY:
            return True
        return False


def exact(value: Any) -> Matcher:
    """Create exact match matcher."""
    return Matcher(MatcherType.EXACT, expected=value)


def type_match(expected_type: type) -> Matcher:
    """Create type match matcher."""
    return Matcher(MatcherType.TYPE, expected=expected_type)


def regex(pattern: str) -> Matcher:
    """Create regex match matcher."""
    return Matcher(MatcherType.REGEX, pattern=pattern)


def range_match(min_val: Any = None, max_val: Any = None) -> Matcher:
    """Create range match matcher."""
    return Matcher(MatcherType.RANGE, min_value=min_val, max_value=max_val)


def contains(value: Any) -> Matcher:
    """Create contains matcher."""
    return Matcher(MatcherType.CONTAINS, expected=value)


def any_value() -> Matcher:
    """Create any value matcher."""
    return Matcher(MatcherType.ANY)
