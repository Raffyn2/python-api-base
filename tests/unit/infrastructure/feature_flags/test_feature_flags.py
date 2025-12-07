"""Unit tests for feature flags.

Tests FlagStatus, EvaluationContext, FeatureFlag, EvaluationResult,
FeatureFlagEvaluator, InMemoryFeatureFlagStore, and FlagAuditLogger.
"""

from datetime import UTC, datetime

import pytest

from infrastructure.feature_flags.flags import (
    EvaluationContext,
    EvaluationResult,
    FeatureFlag,
    FeatureFlagEvaluator,
    FlagAuditLogger,
    FlagEvaluationLog,
    FlagStatus,
    InMemoryFeatureFlagStore,
)


class TestFlagStatus:
    """Tests for FlagStatus enum."""

    def test_enabled_value(self) -> None:
        """Test ENABLED value."""
        assert FlagStatus.ENABLED.value == "enabled"

    def test_disabled_value(self) -> None:
        """Test DISABLED value."""
        assert FlagStatus.DISABLED.value == "disabled"

    def test_percentage_value(self) -> None:
        """Test PERCENTAGE value."""
        assert FlagStatus.PERCENTAGE.value == "percentage"

    def test_targeted_value(self) -> None:
        """Test TARGETED value."""
        assert FlagStatus.TARGETED.value == "targeted"


class TestEvaluationContext:
    """Tests for EvaluationContext dataclass."""

    def test_default_values(self) -> None:
        """Test default context values."""
        context = EvaluationContext[dict]()
        
        assert context.user_id is None
        assert context.groups == ()
        assert context.attributes == {}
        assert context.context_data is None

    def test_with_user_id(self) -> None:
        """Test context with user ID."""
        context = EvaluationContext[dict](user_id="user-123")
        
        assert context.user_id == "user-123"

    def test_with_groups(self) -> None:
        """Test context with groups."""
        context = EvaluationContext[dict](groups=("admin", "beta"))
        
        assert context.groups == ("admin", "beta")

    def test_with_attributes(self) -> None:
        """Test context with attributes."""
        context = EvaluationContext[dict](
            attributes={"country": "US", "plan": "premium"}
        )
        
        assert context.attributes["country"] == "US"
        assert context.attributes["plan"] == "premium"

    def test_immutability(self) -> None:
        """Test context is immutable."""
        context = EvaluationContext[dict](user_id="user-123")
        
        with pytest.raises(AttributeError):
            context.user_id = "other"  # type: ignore


class TestFeatureFlag:
    """Tests for FeatureFlag dataclass."""

    def test_creation(self) -> None:
        """Test flag creation."""
        flag = FeatureFlag[dict](
            key="new-feature",
            name="New Feature",
        )
        
        assert flag.key == "new-feature"
        assert flag.name == "New Feature"
        assert flag.status == FlagStatus.DISABLED

    def test_is_enabled_for_disabled_flag(self) -> None:
        """Test disabled flag returns False."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.DISABLED,
        )
        context = EvaluationContext[dict](user_id="user-123")
        
        assert flag.is_enabled_for(context) is False

    def test_is_enabled_for_enabled_flag(self) -> None:
        """Test enabled flag returns True."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.ENABLED,
        )
        context = EvaluationContext[dict](user_id="user-123")
        
        assert flag.is_enabled_for(context) is True

    def test_is_enabled_for_disabled_user(self) -> None:
        """Test disabled user returns False even if flag enabled."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.ENABLED,
            disabled_users={"user-123"},
        )
        context = EvaluationContext[dict](user_id="user-123")
        
        assert flag.is_enabled_for(context) is False

    def test_is_enabled_for_targeted_user(self) -> None:
        """Test targeted user returns True."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.TARGETED,
            enabled_users={"user-123"},
        )
        context = EvaluationContext[dict](user_id="user-123")
        
        assert flag.is_enabled_for(context) is True

    def test_is_enabled_for_targeted_group(self) -> None:
        """Test targeted group returns True."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.TARGETED,
            enabled_groups={"beta"},
        )
        context = EvaluationContext[dict](user_id="user-123", groups=("beta",))
        
        assert flag.is_enabled_for(context) is True

    def test_is_enabled_for_not_in_target(self) -> None:
        """Test user not in target returns False."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.TARGETED,
            enabled_groups={"beta"},
        )
        context = EvaluationContext[dict](user_id="user-123", groups=("alpha",))
        
        assert flag.is_enabled_for(context) is False

    def test_percentage_rollout(self) -> None:
        """Test percentage rollout is consistent."""
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.PERCENTAGE,
            percentage=50.0,
        )
        
        # Same user should always get same result
        context = EvaluationContext[dict](user_id="user-123")
        result1 = flag.is_enabled_for(context)
        result2 = flag.is_enabled_for(context)
        
        assert result1 == result2


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_creation(self) -> None:
        """Test result creation."""
        result = EvaluationResult(
            flag_key="test",
            enabled=True,
            reason="FLAG_ENABLED",
        )
        
        assert result.flag_key == "test"
        assert result.enabled is True
        assert result.reason == "FLAG_ENABLED"
        assert result.variant is None
        assert result.metadata == {}

    def test_with_variant(self) -> None:
        """Test result with variant."""
        result = EvaluationResult(
            flag_key="test",
            enabled=True,
            reason="VARIANT_SELECTED",
            variant="control",
        )
        
        assert result.variant == "control"


class TestFeatureFlagEvaluator:
    """Tests for FeatureFlagEvaluator."""

    def test_register_flag(self) -> None:
        """Test registering a flag."""
        evaluator = FeatureFlagEvaluator[dict]()
        flag = FeatureFlag[dict](key="test", name="Test")
        
        evaluator.register(flag)
        
        assert "test" in evaluator._flags

    def test_evaluate_not_found(self) -> None:
        """Test evaluating non-existent flag."""
        evaluator = FeatureFlagEvaluator[dict]()
        context = EvaluationContext[dict](user_id="user-123")
        
        result = evaluator.evaluate("nonexistent", context)
        
        assert result.enabled is False
        assert result.reason == "FLAG_NOT_FOUND"

    def test_evaluate_enabled(self) -> None:
        """Test evaluating enabled flag."""
        evaluator = FeatureFlagEvaluator[dict]()
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.ENABLED,
        )
        evaluator.register(flag)
        context = EvaluationContext[dict](user_id="user-123")
        
        result = evaluator.evaluate("test", context)
        
        assert result.enabled is True
        assert result.reason == "FLAG_ENABLED"

    def test_is_enabled(self) -> None:
        """Test is_enabled shortcut."""
        evaluator = FeatureFlagEvaluator[dict]()
        flag = FeatureFlag[dict](
            key="test",
            name="Test",
            status=FlagStatus.ENABLED,
        )
        evaluator.register(flag)
        context = EvaluationContext[dict](user_id="user-123")
        
        assert evaluator.is_enabled("test", context) is True


class TestInMemoryFeatureFlagStore:
    """Tests for InMemoryFeatureFlagStore."""

    @pytest.fixture
    def store(self) -> InMemoryFeatureFlagStore[dict]:
        """Create a fresh store."""
        return InMemoryFeatureFlagStore[dict]()

    @pytest.mark.asyncio
    async def test_save_and_get(self, store: InMemoryFeatureFlagStore[dict]) -> None:
        """Test saving and getting a flag."""
        flag = FeatureFlag[dict](key="test", name="Test")
        
        await store.save(flag)
        result = await store.get("test")
        
        assert result is not None
        assert result.key == "test"

    @pytest.mark.asyncio
    async def test_get_not_found(self, store: InMemoryFeatureFlagStore[dict]) -> None:
        """Test getting non-existent flag."""
        result = await store.get("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, store: InMemoryFeatureFlagStore[dict]) -> None:
        """Test getting all flags."""
        flag1 = FeatureFlag[dict](key="test1", name="Test 1")
        flag2 = FeatureFlag[dict](key="test2", name="Test 2")
        
        await store.save(flag1)
        await store.save(flag2)
        
        result = await store.get_all()
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete(self, store: InMemoryFeatureFlagStore[dict]) -> None:
        """Test deleting a flag."""
        flag = FeatureFlag[dict](key="test", name="Test")
        await store.save(flag)
        
        result = await store.delete("test")
        
        assert result is True
        assert await store.get("test") is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, store: InMemoryFeatureFlagStore[dict]) -> None:
        """Test deleting non-existent flag."""
        result = await store.delete("nonexistent")
        
        assert result is False


class TestFlagAuditLogger:
    """Tests for FlagAuditLogger."""

    def test_log_evaluation(self) -> None:
        """Test logging an evaluation."""
        logger = FlagAuditLogger()
        result = EvaluationResult(
            flag_key="test",
            enabled=True,
            reason="FLAG_ENABLED",
        )
        context = EvaluationContext[dict](user_id="user-123")
        
        logger.log_evaluation(result, context)
        
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].flag_key == "test"
        assert logs[0].result is True

    def test_get_logs_filtered(self) -> None:
        """Test getting logs filtered by flag key."""
        logger = FlagAuditLogger()
        
        result1 = EvaluationResult(flag_key="flag1", enabled=True, reason="ENABLED")
        result2 = EvaluationResult(flag_key="flag2", enabled=False, reason="DISABLED")
        context = EvaluationContext[dict](user_id="user-123")
        
        logger.log_evaluation(result1, context)
        logger.log_evaluation(result2, context)
        
        logs = logger.get_logs("flag1")
        
        assert len(logs) == 1
        assert logs[0].flag_key == "flag1"
