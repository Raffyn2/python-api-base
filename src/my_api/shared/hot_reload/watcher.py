"""File watcher for detecting code changes.

**Feature: file-size-compliance-phase2, Task 2.2**
**Validates: Requirements 1.2, 5.1, 5.2, 5.3**
"""

import hashlib
import time
from pathlib import Path

from .enums import FileChangeType
from .models import FileChange, WatchConfig


class FileHasher:
    """Computes and caches file hashes for change detection."""

    def __init__(self) -> None:
        """Initialize hasher."""
        self._cache: dict[Path, str] = {}

    def compute_hash(self, path: Path) -> str | None:
        """Compute MD5 hash of file contents (not for security)."""
        try:
            content = path.read_bytes()
            return hashlib.md5(content, usedforsecurity=False).hexdigest()
        except (OSError, IOError):
            return None

    def has_changed(self, path: Path) -> tuple[bool, str | None, str | None]:
        """Check if file has changed since last check."""
        old_hash = self._cache.get(path)
        new_hash = self.compute_hash(path)

        if new_hash is None:
            if old_hash is not None:
                del self._cache[path]
                return True, old_hash, None
            return False, None, None

        if old_hash != new_hash:
            self._cache[path] = new_hash
            return True, old_hash, new_hash

        return False, old_hash, new_hash

    def update_hash(self, path: Path) -> str | None:
        """Update cached hash for a file."""
        new_hash = self.compute_hash(path)
        if new_hash:
            self._cache[path] = new_hash
        return new_hash

    def clear(self) -> None:
        """Clear all cached hashes."""
        self._cache.clear()


class FileWatcher:
    """Watches files for changes."""

    def __init__(self, config: WatchConfig) -> None:
        """Initialize watcher with config."""
        self._config = config
        self._hasher = FileHasher()
        self._known_files: set[Path] = set()
        self._last_check = time.time()

    def _matches_pattern(self, path: Path, patterns: list[str]) -> bool:
        """Check if path matches any of the patterns."""
        name = path.name
        for pattern in patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in str(path):
                return True
            elif name == pattern:
                return True
        return False

    def _should_watch(self, path: Path) -> bool:
        """Determine if a file should be watched."""
        if not path.is_file():
            return False
        if self._matches_pattern(path, self._config.exclude_patterns):
            return False
        if not self._matches_pattern(path, self._config.include_patterns):
            return False
        return True

    def _scan_directory(self, directory: Path) -> set[Path]:
        """Scan directory for watchable files."""
        files: set[Path] = set()
        try:
            for item in directory.rglob("*"):
                if self._should_watch(item):
                    files.add(item)
        except (OSError, PermissionError):
            pass
        return files

    def scan_all(self) -> set[Path]:
        """Scan all watch paths for files."""
        all_files: set[Path] = set()
        for watch_path in self._config.watch_paths:
            if watch_path.is_dir():
                all_files.update(self._scan_directory(watch_path))
            elif watch_path.is_file() and self._should_watch(watch_path):
                all_files.add(watch_path)
        return all_files

    def initialize(self) -> int:
        """Initialize watcher by scanning all files."""
        self._known_files = self.scan_all()
        for file_path in self._known_files:
            self._hasher.update_hash(file_path)
        return len(self._known_files)

    def check_changes(self) -> list[FileChange]:
        """Check for file changes since last check."""
        current_time = time.time()
        if (current_time - self._last_check) * 1000 < self._config.debounce_ms:
            return []

        self._last_check = current_time
        changes: list[FileChange] = []
        current_files = self.scan_all()

        new_files = current_files - self._known_files
        for path in new_files:
            new_hash = self._hasher.update_hash(path)
            changes.append(
                FileChange(
                    path=path,
                    change_type=FileChangeType.CREATED,
                    new_hash=new_hash,
                )
            )

        deleted_files = self._known_files - current_files
        for path in deleted_files:
            changes.append(
                FileChange(
                    path=path,
                    change_type=FileChangeType.DELETED,
                    old_hash=self._hasher._cache.get(path),
                )
            )
            if path in self._hasher._cache:
                del self._hasher._cache[path]

        for path in current_files & self._known_files:
            changed, old_hash, new_hash = self._hasher.has_changed(path)
            if changed:
                changes.append(
                    FileChange(
                        path=path,
                        change_type=FileChangeType.MODIFIED,
                        old_hash=old_hash,
                        new_hash=new_hash,
                    )
                )

        self._known_files = current_files
        return changes
