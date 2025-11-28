"""Fuzzing configuration.

**Feature: code-review-refactoring, Task 16.3: Refactor fuzzing.py**
**Validates: Requirements 5.3**
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FuzzingConfig:
    """Configuration for fuzzing."""

    max_iterations: int = 10000
    timeout_seconds: float = 1.0
    max_input_size: int = 4096
    min_input_size: int = 1
    corpus_dir: Path = field(default_factory=lambda: Path("corpus"))
    crashes_dir: Path = field(default_factory=lambda: Path("crashes"))
    seed: int | None = None
    minimize_crashes: bool = True
    coverage_guided: bool = True

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors: list[str] = []
        if self.max_iterations < 1:
            errors.append("max_iterations must be >= 1")
        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be > 0")
        if self.max_input_size < self.min_input_size:
            errors.append("max_input_size must be >= min_input_size")
        if self.min_input_size < 0:
            errors.append("min_input_size must be >= 0")
        return errors
