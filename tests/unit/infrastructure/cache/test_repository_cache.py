"""Unit tests for repository caching decorator.

**Task: Phase 4 - Infrastructure Layer Tests**
**Requirements: Repository caching with automatic invalidation**
"""

from infrastructure.cache.repository import (
    RepositoryCacheConfig,
    _get_entity_name,
    _make_cache_key,
)


class TestRepositoryCacheConfig:
    """Tests for RepositoryCacheConfig."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        config = RepositoryCacheConfig()

        assert config.ttl == 300
        assert config.enabled is True
        assert config.key_prefix == "repo"
        assert config.log_hits is False
        assert config.log_misses is False

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = RepositoryCacheConfig(
            ttl=600,
            enabled=False,
            key_prefix="custom",
            log_hits=True,
            log_misses=True,
        )

        assert config.ttl == 600
        assert config.enabled is False
        assert config.key_prefix == "custom"
        assert config.log_hits is True
        assert config.log_misses is True


class TestGetEntityName:
    """Tests for _get_entity_name helper."""

    def test_extracts_from_repository_suffix(self) -> None:
        """Should extract entity name from Repository suffix."""

        class UserRepository:
            pass

        repo = UserRepository()
        result = _get_entity_name(repo)

        assert result == "User"

    def test_handles_no_repository_suffix(self) -> None:
        """Should return class name if no Repository suffix."""

        class UserStore:
            pass

        repo = UserStore()
        result = _get_entity_name(repo)

        assert result == "UserStore"


class TestMakeCacheKey:
    """Tests for _make_cache_key helper."""

    def test_get_by_id_key(self) -> None:
        """Should create key for get_by_id."""
        result = _make_cache_key("repo", "User", "get_by_id", "user-123")

        assert result == "repo:User:get_by_id:user-123"

    def test_get_all_key_with_args(self) -> None:
        """Should create key for get_all with args."""
