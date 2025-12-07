"""Tests for cache invalidation strategy.

Tests InvalidationRule, CacheInvalidationStrategy, and related components.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from application.common.middleware.cache.cache_invalidation import (
    CacheInvalidationMiddleware,
    CacheInvalidationStrategy,
    CompositeCacheInvalidationStrategy,
    InvalidationRule,
    create_entity_specific_pattern,
    create_query_type_pattern,
)


class MockQueryCache:
    """Mock query cache for testing."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self.clear_pattern_calls: list[str] = []

    async def clear_pattern(self, pattern: str) -> int:
        self.clear_pattern_calls.append(pattern)
        # Simulate clearing matching keys
        return 1


@dataclass
class UserCreatedEvent:
    """Sample user created event."""

    user_id: str


@dataclass
class UserUpdatedEvent:
    """Sample user updated event."""

    user_id: str


@dataclass
class ItemCreatedEvent:
    """Sample item created event."""

    item_id: str


class TestInvalidationRule:
    """Tests for InvalidationRule."""

    def test_create_rule(self) -> None:
        rule = InvalidationRule(
            event_type=UserCreatedEvent,
            patterns=["query_cache:ListUsers:*"],
        )
        assert rule.event_type == UserCreatedEvent
        assert "query_cache:ListUsers:*" in rule.patterns
        assert rule.log_invalidation is True

    def test_rule_is_frozen(self) -> None:
        rule = InvalidationRule(
            event_type=UserCreatedEvent,
            patterns=["pattern"],
        )
        with pytest.raises(AttributeError):
            rule.patterns = []  # type: ignore

    def test_rule_with_logging_disabled(self) -> None:
        rule = InvalidationRule(
            event_type=UserCreatedEvent,
            patterns=["pattern"],
            log_invalidation=False,
        )
        assert rule.log_invalidation is False


class SampleCacheInvalidationStrategy(CacheInvalidationStrategy):
    """Sample strategy for testing."""

    def __init__(self, cache: MockQueryCache) -> None:
        super().__init__(cache)
        self.add_rule(
            InvalidationRule(
                event_type=UserCreatedEvent,
                patterns=["query_cache:ListUsers:*"],
            )
        )
        self.add_rule(
            InvalidationRule(
                event_type=UserUpdatedEvent,
                patterns=[
                    "query_cache:GetUser:*",
                    "query_cache:ListUsers:*",
                ],
            )
        )


class TestCacheInvalidationStrategy:
    """Tests for CacheInvalidationStrategy."""

    @pytest.fixture
    def cache(self) -> MockQueryCache:
        return MockQueryCache()

    @pytest.fixture
    def strategy(self, cache: MockQueryCache) -> SampleCacheInvalidationStrategy:
        return SampleCacheInvalidationStrategy(cache)

    def test_add_rule(self, cache: MockQueryCache) -> None:
        strategy = SampleCacheInvalidationStrategy(cache)
        assert UserCreatedEvent in strategy._rules
        assert UserUpdatedEvent in strategy._rules

    @pytest.mark.asyncio
    async def test_invalidate_clears_patterns(
        self, cache: MockQueryCache, strategy: SampleCacheInvalidationStrategy
    ) -> None:
        event = UserCreatedEvent(user_id="123")
        await strategy.invalidate(event)

        assert "query_cache:ListUsers:*" in cache.clear_pattern_calls

    @pytest.mark.asyncio
    async def test_invalidate_multiple_patterns(
        self, cache: MockQueryCache, strategy: SampleCacheInvalidationStrategy
    ) -> None:
        event = UserUpdatedEvent(user_id="123")
        await strategy.invalidate(event)

        assert "query_cache:GetUser:*" in cache.clear_pattern_calls
        assert "query_cache:ListUsers:*" in cache.clear_pattern_calls

    @pytest.mark.asyncio
    async def test_invalidate_unknown_event_does_nothing(
        self, cache: MockQueryCache, strategy: SampleCacheInvalidationStrategy
    ) -> None:
        event = ItemCreatedEvent(item_id="456")
        await strategy.invalidate(event)

        assert len(cache.clear_pattern_calls) == 0


class TestCompositeCacheInvalidationStrategy:
    """Tests for CompositeCacheInvalidationStrategy."""

    @pytest.fixture
    def cache(self) -> MockQueryCache:
        return MockQueryCache()

    def test_add_strategy(self, cache: MockQueryCache) -> None:
        composite = CompositeCacheInvalidationStrategy(cache)
        strategy = SampleCacheInvalidationStrategy(cache)
        composite.add_strategy(strategy)

        assert len(composite._strategies) == 1

    @pytest.mark.asyncio
    async def test_on_event_delegates_to_strategies(
        self, cache: MockQueryCache
    ) -> None:
        composite = CompositeCacheInvalidationStrategy(cache)
        strategy = SampleCacheInvalidationStrategy(cache)
        composite.add_strategy(strategy)

        event = UserCreatedEvent(user_id="123")
        await composite.on_event(event)

        assert "query_cache:ListUsers:*" in cache.clear_pattern_calls

    @pytest.mark.asyncio
    async def test_multiple_strategies(self, cache: MockQueryCache) -> None:
        composite = CompositeCacheInvalidationStrategy(cache)

        # Add two strategies
        strategy1 = SampleCacheInvalidationStrategy(cache)
        strategy2 = SampleCacheInvalidationStrategy(cache)
        composite.add_strategy(strategy1)
        composite.add_strategy(strategy2)

        event = UserCreatedEvent(user_id="123")
        await composite.on_event(event)

        # Both strategies should have been called
        assert cache.clear_pattern_calls.count("query_cache:ListUsers:*") == 2


class TestCacheInvalidationMiddleware:
    """Tests for CacheInvalidationMiddleware."""

    @pytest.fixture
    def cache(self) -> MockQueryCache:
        return MockQueryCache()

    @dataclass
    class CreateUserCommand:
        name: str

    @dataclass
    class UpdateUserCommand:
        user_id: str
        name: str

    @dataclass
    class DeleteItemCommand:
        item_id: str

    @pytest.mark.asyncio
    async def test_invalidates_after_command(self, cache: MockQueryCache) -> None:
        middleware = CacheInvalidationMiddleware(
            cache,
            invalidation_map={
                self.CreateUserCommand: ["query_cache:ListUsers:*"],
            },
        )

        command = self.CreateUserCommand(name="John")

        async def handler(cmd: Any) -> str:
            return "created"

        result = await middleware(command, handler)
        assert result == "created"
        assert "query_cache:ListUsers:*" in cache.clear_pattern_calls

    @pytest.mark.asyncio
    async def test_invalidates_multiple_patterns(self, cache: MockQueryCache) -> None:
        middleware = CacheInvalidationMiddleware(
            cache,
            invalidation_map={
                self.UpdateUserCommand: [
                    "query_cache:GetUser:*",
                    "query_cache:ListUsers:*",
                ],
            },
        )

        command = self.UpdateUserCommand(user_id="123", name="Jane")

        async def handler(cmd: Any) -> str:
            return "updated"

        await middleware(command, handler)
        assert "query_cache:GetUser:*" in cache.clear_pattern_calls
        assert "query_cache:ListUsers:*" in cache.clear_pattern_calls

    @pytest.mark.asyncio
    async def test_no_invalidation_for_unmapped_command(
        self, cache: MockQueryCache
    ) -> None:
        middleware = CacheInvalidationMiddleware(
            cache,
            invalidation_map={
                self.CreateUserCommand: ["query_cache:ListUsers:*"],
            },
        )

        command = self.DeleteItemCommand(item_id="456")

        async def handler(cmd: Any) -> str:
            return "deleted"

        await middleware(command, handler)
        assert len(cache.clear_pattern_calls) == 0


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_entity_specific_pattern(self) -> None:
        pattern = create_entity_specific_pattern("GetUserQuery", "user-123")
        assert pattern == "query_cache:GetUserQuery:*user-123*"

    def test_create_entity_specific_pattern_custom_prefix(self) -> None:
        pattern = create_entity_specific_pattern(
            "GetUserQuery", "user-123", prefix="custom"
        )
        assert pattern == "custom:GetUserQuery:*user-123*"

    def test_create_query_type_pattern(self) -> None:
        pattern = create_query_type_pattern("ListUsersQuery")
        assert pattern == "query_cache:ListUsersQuery:*"

    def test_create_query_type_pattern_custom_prefix(self) -> None:
        pattern = create_query_type_pattern("ListUsersQuery", prefix="cache")
        assert pattern == "cache:ListUsersQuery:*"
