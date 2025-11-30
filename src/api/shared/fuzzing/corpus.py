"""Corpus and crash management.

**Feature: code-review-refactoring, Task 16.3: Refactor fuzzing.py**
**Validates: Requirements 5.3**
"""

import json
from pathlib import Path

from .enums import CrashType
from .models import CrashInfo, FuzzInput


class CorpusManager:
    """Manages fuzzing corpus (seed inputs)."""

    def __init__(self, corpus_dir: Path) -> None:
        self._corpus_dir = corpus_dir
        self._inputs: dict[str, FuzzInput] = {}
        self._load_corpus()

    def _load_corpus(self) -> None:
        """Load corpus from disk."""
        if not self._corpus_dir.exists():
            self._corpus_dir.mkdir(parents=True, exist_ok=True)
            return
        for file_path in self._corpus_dir.glob("*"):
            if file_path.is_file():
                try:
                    data = file_path.read_bytes()
                    fuzz_input = FuzzInput(data=data, source="corpus")
                    self._inputs[fuzz_input.hash] = fuzz_input
                except OSError:
                    pass

    def add(self, fuzz_input: FuzzInput) -> bool:
        """Add input to corpus. Returns True if new."""
        if fuzz_input.hash in self._inputs:
            return False
        self._inputs[fuzz_input.hash] = fuzz_input
        self._save_input(fuzz_input)
        return True

    def _save_input(self, fuzz_input: FuzzInput) -> None:
        """Save input to disk."""
        file_path = self._corpus_dir / fuzz_input.hash[:16]
        file_path.write_bytes(fuzz_input.data)

    def get_all(self) -> list[FuzzInput]:
        """Get all corpus inputs."""
        return list(self._inputs.values())

    def get_by_hash(self, hash_prefix: str) -> FuzzInput | None:
        """Get input by hash prefix."""
        for h, inp in self._inputs.items():
            if h.startswith(hash_prefix):
                return inp
        return None

    def size(self) -> int:
        """Get corpus size."""
        return len(self._inputs)

    def clear(self) -> None:
        """Clear corpus."""
        self._inputs.clear()
        for file_path in self._corpus_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()


class CrashManager:
    """Manages crash inputs and deduplication."""

    def __init__(self, crashes_dir: Path) -> None:
        self._crashes_dir = crashes_dir
        self._crashes: dict[str, CrashInfo] = {}
        self._crashes_dir.mkdir(parents=True, exist_ok=True)

    def add(self, crash: CrashInfo) -> bool:
        """Add crash. Returns True if new."""
        if crash.crash_id in self._crashes:
            return False
        self._crashes[crash.crash_id] = crash
        self._save_crash(crash)
        return True

    def _save_crash(self, crash: CrashInfo) -> None:
        """Save crash to disk."""
        crash_dir = self._crashes_dir / crash.crash_id
        crash_dir.mkdir(exist_ok=True)
        (crash_dir / "input").write_bytes(crash.input_data.data)
        (crash_dir / "info.json").write_text(json.dumps(crash.to_dict(), indent=2))

    def get_all(self) -> list[CrashInfo]:
        """Get all crashes."""
        return list(self._crashes.values())

    def get_by_type(self, crash_type: CrashType) -> list[CrashInfo]:
        """Get crashes by type."""
        return [c for c in self._crashes.values() if c.crash_type == crash_type]

    def count(self) -> int:
        """Get crash count."""
        return len(self._crashes)
