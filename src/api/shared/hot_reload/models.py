"""Hot reload data models.

**Feature: file-size-compliance-phase2, Task 2.2**
**Validates: Requirements 1.2, 5.1, 5.2, 5.3**
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .enums import FileChangeType, ReloadStrategy


@dataclass
class FileChange:
    """Represents a detected file change."""

    path: Path
    change_type: FileChangeType
    timestamp: datetime = field(default_factory=datetime.now)
    old_hash: str | None = None
    new_hash: str | None = None


@dataclass
class WatchConfig:
    """Configuration for file watching."""

    watch_paths: list[Path] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=lambda: ["*.py"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["__pycache__", "*.pyc", ".git", ".venv", "venv"]
    )
    debounce_ms: int = 100
    strategy: ReloadStrategy = ReloadStrategy.CHANGED


@dataclass
class ReloadResult:
    """Result of a reload operation."""

    success: bool
    reloaded_modules: list[str] = field(default_factory=list)
    failed_modules: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
