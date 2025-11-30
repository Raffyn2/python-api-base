"""Contract verification reports.

**Feature: code-review-refactoring, Task 17.1: Refactor contract_testing.py**
**Validates: Requirements 5.4**
"""

from dataclasses import dataclass, field
from datetime import datetime

from .enums import ContractStatus


@dataclass
class ContractVerificationResult:
    """Result of verifying a single interaction."""

    interaction: str
    status: ContractStatus
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContractReport:
    """Full report of contract verification."""

    contract_name: str
    consumer: str
    provider: str
    results: list[ContractVerificationResult] = field(default_factory=list)
    total_interactions: int = 0
    passed: int = 0
    failed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_interactions == 0:
            return 100.0
        return (self.passed / self.total_interactions) * 100

    @property
    def all_passed(self) -> bool:
        """Check if all interactions passed."""
        return self.failed == 0
