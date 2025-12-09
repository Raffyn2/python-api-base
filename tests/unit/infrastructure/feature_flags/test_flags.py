"""Unit tests for infrastructure/feature_flags/flags.py.

Tests feature flag evaluation.

**Task 22.1: Create tests for flags.py**
**Requirements: 4.5**
"""

import pytest

from infrastructure.feature_flags.flags import (
    EvaluationContext,
    EvaluationResult,
    FeatureFlag,
    FeatureFlagEvaluator,
    FlagAuditLogger,
    FlagStatus,
    InMemoryFeatureFlagStore,
)


class TestFlagStatus:
    """Tests for FlagStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert FlagStatus.ENABLED.value == "enabled"
        assert FlagStatus.DISABLED.value == "disabled"
        assert FlagStatus.PERCENTAGE.value == "percentage"
        assert FlagStatus.TARGETED.value == "targeted"


class TestEvaluationContext:
    """Tests for EvaluationContext."""

    def test_create_context(self) -> None:
        """Test creating evaluation context."""
        ctx = EvaluationContext[dict](
            user_id="user-123",
            groups=("beta", "premium"),
            attributes={"country": "US"},
        )

        assert ctx.user_id == "user-123"
        assert "beta" in ctx.groups
        assert ctx.attributes["country"] == "US"

    def test_context_immutability(self) -> None:
        """Test context is immutable."""
        ctx = EvaluationContext[dict](user_id="user-123")

        with pytest.raises(AttributeError):
            ctx.user_id = "new-id"


class TestFeatureFlag:
    """Tests for FeatureFlag."""

    def test_create_flag(self) -> None:
        """Test creating feature flag."""
        flag = FeatureFlag[dict](
            key="new-feature",
            name="New Feature",
            description="A new feature",
            status=FlagStatus.ENABLED,
        )

        assert flag.key == "new-feature"
        assert flag.status == FlagStatus.ENABLED

    def test_enabled_flag(self) -> None:
        """Test enabled flag returns True."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.ENABLED,
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        assert flag.is_enabled_for(ctx) is True

    def test_disabled_flag(self) -> None:
        """Test disabled flag returns False."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.DISABLED,
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        assert flag.is_enabled_for(ctx) is False


class TestFeatureFlagTargeting:
    """Tests for feature flag targeting."""

    def test_user_targeting_enabled(self) -> None:
        """Test user targeting enables flag."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.TARGETED,
            enabled_users={"user-123"},
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        assert flag.is_enabled_for(ctx) is True

    def test_user_targeting_not_in_list(self) -> None:
        """Test user not in targeting list."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.TARGETED,
            enabled_users={"user-456"},
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        assert flag.is_enabled_for(ctx) is False

    def test_user_disabled_overrides(self) -> None:
        """Test disabled user overrides enabled status."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.ENABLED,
            disabled_users={"user-123"},
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        assert flag.is_enabled_for(ctx) is False

    def test_group_targeting(self) -> None:
        """Test group targeting."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.TARGETED,
            enabled_groups={"beta"},
        )
        ctx = EvaluationContext[dict](user_id="user-123", groups=("beta",))

        assert flag.is_enabled_for(ctx) is True

    def test_percentage_rollout(self) -> None:
        """Test percentage rollout is deterministic."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.PERCENTAGE,
            percentage=50.0,
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        # Same user should get same result
        result1 = flag.is_enabled_for(ctx)
        result2 = flag.is_enabled_for(ctx)

        assert result1 == result2


class TestFeatureFlagEvaluator:
    """Tests for FeatureFlagEvaluator."""

    def test_evaluate_enabled_flag(self) -> None:
        """Test evaluating enabled flag."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.ENABLED,
        )
        evaluator = FeatureFlagEvaluator[dict]({"feature": flag})
        ctx = EvaluationContext[dict](user_id="user-123")

        result = evaluator.evaluate("feature", ctx)

        assert result.enabled is True
        assert result.reason == "FLAG_ENABLED"

    def test_evaluate_nonexistent_flag(self) -> None:
        """Test evaluating nonexistent flag."""
        evaluator = FeatureFlagEvaluator[dict]()
        ctx = EvaluationContext[dict](user_id="user-123")

        result = evaluator.evaluate("nonexistent", ctx)

        assert result.enabled is False
        assert result.reason == "FLAG_NOT_FOUND"

    def test_register_flag(self) -> None:
        """Test registering a flag."""
        evaluator = FeatureFlagEvaluator[dict]()
        flag = FeatureFlag[dict](
            key="new-feature",
            name="New Feature",
            status=FlagStatus.ENABLED,
        )

        evaluator.register(flag)
        ctx = EvaluationContext[dict](user_id="user-123")

        assert evaluator.is_enabled("new-feature", ctx) is True

    def test_is_enabled_shortcut(self) -> None:
        """Test is_enabled shortcut method."""
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.ENABLED,
        )
        evaluator = FeatureFlagEvaluator[dict]({"feature": flag})
        ctx = EvaluationContext[dict](user_id="user-123")

        assert evaluator.is_enabled("feature", ctx) is True


class TestInMemoryFeatureFlagStore:
    """Tests for InMemoryFeatureFlagStore."""

    @pytest.mark.asyncio
    async def test_save_and_get(self) -> None:
        """Test saving and getting flag."""
        store = InMemoryFeatureFlagStore[dict]()
        flag = FeatureFlag[dict](
            key="feature",
            name="Feature",
            status=FlagStatus.ENABLED,
        )

        await store.save(flag)
        retrieved = await store.get("feature")

        assert retrieved is not None
        assert retrieved.key == "feature"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self) -> None:
        """Test getting nonexistent flag."""
        store = InMemoryFeatureFlagStore[dict]()

        result = await store.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        """Test getting all flags."""
        store = InMemoryFeatureFlagStore[dict]()
        await store.save(FeatureFlag[dict](key="f1", name="F1"))
        await store.save(FeatureFlag[dict](key="f2", name="F2"))

        flags = await store.get_all()

        assert len(flags) == 2

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test deleting flag."""
        store = InMemoryFeatureFlagStore[dict]()
        await store.save(FeatureFlag[dict](key="feature", name="Feature"))

        result = await store.delete("feature")

        assert result is True
        assert await store.get("feature") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        """Test deleting nonexistent flag."""
        store = InMemoryFeatureFlagStore[dict]()

        result = await store.delete("nonexistent")

        assert result is False


class TestFlagAuditLogger:
    """Tests for FlagAuditLogger."""

    def test_log_evaluation(self) -> None:
        """Test logging evaluation."""
        logger = FlagAuditLogger()
        result = EvaluationResult(
            flag_key="feature",
            enabled=True,
            reason="FLAG_ENABLED",
        )
        ctx = EvaluationContext[dict](user_id="user-123")

        logger.log_evaluation(result, ctx)

        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].flag_key == "feature"

    def test_get_logs_filtered(self) -> None:
        """Test getting logs filtered by flag key."""
        logger = FlagAuditLogger()
        ctx = EvaluationContext[dict](user_id="user-123")

        logger.log_evaluation(
            EvaluationResult(flag_key="f1", enabled=True, reason="OK"), ctx
        )
        logger.log_evaluation(
            EvaluationResult(flag_key="f2", enabled=False, reason="OFF"), ctx
        )

        logs = logger.get_logs("f1")

        assert len(logs) == 1
        assert logs[0].flag_key == "f1"
