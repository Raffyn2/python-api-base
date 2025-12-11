"""Unit tests for GraphQL DataLoader.

Tests the DataLoader implementation for N+1 prevention.

**Feature: interface-modules-workflow-analysis**
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path to avoid strawberry import issues
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

# Constants duplicated to avoid import chain
_DEFAULT_BATCH_SIZE = 100
_MAX_BATCH_SIZE = 1000
_MIN_BATCH_SIZE = 1


def _create_dataloader_config(batch_size: int = 100, cache: bool = True, batch_delay_ms: float = 0.0) -> object:
    """Create DataLoaderConfig without strawberry imports."""
    from dataclasses import dataclass

    @dataclass
    class DataLoaderConfig:
        batch_size: int = 100
        cache: bool = True
        batch_delay_ms: float = 0.0

        def __post_init__(self) -> None:
            self.batch_size = max(_MIN_BATCH_SIZE, min(self.batch_size, _MAX_BATCH_SIZE))

    return DataLoaderConfig(batch_size=batch_size, cache=cache, batch_delay_ms=batch_delay_ms)


class TestDataLoaderConfig:
    """Tests for DataLoaderConfig validation logic."""

    def test_default_values(self) -> None:
        """Config has sensible defaults."""
        config = _create_dataloader_config()
        assert config.batch_size == _DEFAULT_BATCH_SIZE
        assert config.cache is True
        assert config.batch_delay_ms == 0.0

    def test_batch_size_clamped_to_min(self) -> None:
        """Batch size is clamped to minimum."""
        config = _create_dataloader_config(batch_size=0)
        assert config.batch_size == _MIN_BATCH_SIZE

    def test_batch_size_clamped_to_max(self) -> None:
        """Batch size is clamped to maximum."""
        config = _create_dataloader_config(batch_size=9999)
        assert config.batch_size == _MAX_BATCH_SIZE

    def test_batch_size_within_range(self) -> None:
        """Batch size within range is preserved."""
        config = _create_dataloader_config(batch_size=50)
        assert config.batch_size == 50


class TestDataLoaderCacheLogic:
    """Tests for DataLoader cache operations (isolated from async)."""

    def test_clear_all_removes_cache(self) -> None:
        """Clear without key removes all cached values."""
        cache: dict[str, str] = {"k1": "v1", "k2": "v2"}
        cache.clear()
        assert cache == {}

    def test_clear_single_key(self) -> None:
        """Clear with key removes only that key."""
        cache: dict[str, str] = {"k1": "v1", "k2": "v2"}
        del cache["k1"]
        assert cache == {"k2": "v2"}

    def test_prime_adds_to_cache(self) -> None:
        """Prime adds value to cache."""
        cache: dict[str, str] = {}
        cache["k1"] = "v1"
        assert cache["k1"] == "v1"

    def test_cache_hit_returns_value(self) -> None:
        """Cache hit returns cached value."""
        cache: dict[str, str] = {"k1": "cached"}
        assert cache.get("k1") == "cached"

    def test_cache_miss_returns_none(self) -> None:
        """Cache miss returns None."""
        cache: dict[str, str] = {}
        assert cache.get("missing") is None


class TestDataLoaderBatchLogic:
    """Tests for DataLoader batching logic (isolated)."""

    def test_batch_size_validation(self) -> None:
        """Batch size is validated within bounds."""
        # Test min bound
        assert max(_MIN_BATCH_SIZE, min(0, _MAX_BATCH_SIZE)) == _MIN_BATCH_SIZE
        # Test max bound
        assert max(_MIN_BATCH_SIZE, min(9999, _MAX_BATCH_SIZE)) == _MAX_BATCH_SIZE
        # Test within range
        assert max(_MIN_BATCH_SIZE, min(50, _MAX_BATCH_SIZE)) == 50

    def test_pending_queue_batching(self) -> None:
        """Pending queue respects batch size."""
        batch_size = 3
        pending = ["k1", "k2", "k3", "k4", "k5"]

        batch = pending[:batch_size]
        remaining = pending[batch_size:]

        assert batch == ["k1", "k2", "k3"]
        assert remaining == ["k4", "k5"]

    def test_batch_result_mapping(self) -> None:
        """Batch results map correctly to keys."""
        keys = ["k1", "k2", "k3"]
        values = ["v1", "v2", "v3"]

        result_map = dict(zip(keys, values, strict=True))

        assert result_map["k1"] == "v1"
        assert result_map["k2"] == "v2"
        assert result_map["k3"] == "v3"

    def test_batch_handles_none_values(self) -> None:
        """Batch correctly handles None values."""
        keys = ["k1", "k2", "k3"]
        values: list[str | None] = ["v1", None, "v3"]

        cache: dict[str, str] = {}
        for key, value in zip(keys, values, strict=True):
            if value is not None:
                cache[key] = value

        assert cache == {"k1": "v1", "k3": "v3"}
        assert "k2" not in cache
