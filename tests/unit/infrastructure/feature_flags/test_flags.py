"""Unit tests for feature flags.

Tests FeatureFlag, FeatureFlagEvaluator, and related types.
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

    def test_enabled_value(self) -> None:
        """Test ENABLED status value."""
        assert FlagStatus.ENABLED.value == "enabled"

    def test_disabled_value(self) -> None:
        """Test DISABLED status value."""
        assert FlagStatus.DISABLED.value == "disabled"

    def test_percentage_value(self) -> None:
        """Test PERCENTAGE status value."""
        assert FlagStatus.PERCENTAGE.value == "percentage"

    def test_targeted_value(self) -> None:
        """Test TARGETED status value."""
        assert FlagStatus.TARGETED.value == "targeted"


class TestEvaluationContext:
    """Tests for EvaluationContext."""

    def test_default_values(self) -> None:
        """Test default context values."""
        ctx: EvaluationContext[None] = EvaluationContext()
        assert ctx.user_id is None
        assert ctx.groups == ()
        assert ctx.attributes == {}
        assert ctx.context_data is None

    def test_with_user_id(self) -> None:
        """Test context with user ID."""
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-123")
        assert ctx.user_id == "user-123"

    def test_with_groups(self) -> None:
        """Test context with groups."""
        ctx: EvaluationContext[None] = EvaluationContext(
            groups=("admin", "beta-testers")
        )
        assert "admin" in ctx.groups
        assert "beta-testers" in ctx.groups

    def test_with_attributes(self) -> None:
        """Test context with attributes."""
        ctx: EvaluationContext[None] = EvaluationContext(
            attributes={"country": "BR", "plan": "premium"}
        )
        assert ctx.attributes["country"] == "BR"

    def test_frozen(self) -> None:
        """Test context is immutable."""
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        with pytest.raises(AttributeError):
            ctx.user_id = "user-2"  # type: ignore[misc]


class TestFeatureFlag:
    """Tests for FeatureFlag."""

    def test_default_values(self) -> None:
        """Test default flag values."""
        flag: FeatureFlag[None] = FeatureFlag(key="test", name="Test Flag")
        assert flag.key == "test"
        assert flag.name == "Test Flag"
        assert flag.status == FlagStatus.DISABLED
        assert flag.percentage == 0.0

    def test_disabled_flag(self) -> None:
        """Test disabled flag returns False."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test", name="Test", status=FlagStatus.DISABLED
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        assert flag.is_enabled_for(ctx) is False

    def test_enabled_flag(self) -> None:
        """Test enabled flag returns True."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test", name="Test", status=FlagStatus.ENABLED
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        assert flag.is_enabled_for(ctx) is True

    def test_user_targeting(self) -> None:
        """Test user targeting."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test",
            name="Test",
            status=FlagStatus.TARGETED,
            enabled_users={"user-1", "user-2"},
        )
        ctx1: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        ctx2: EvaluationContext[None] = EvaluationContext(user_id="user-3")

        assert flag.is_enabled_for(ctx1) is True
        assert flag.is_enabled_for(ctx2) is False

    def test_user_disabled(self) -> None:
        """Test user explicitly disabled."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test",
            name="Test",
            status=FlagStatus.ENABLED,
            disabled_users={"blocked-user"},
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="blocked-user")
        assert flag.is_enabled_for(ctx) is False

    def test_group_targeting(self) -> None:
        """Test group targeting."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test",
            name="Test",
            status=FlagStatus.TARGETED,
            enabled_groups={"beta-testers"},
        )
        ctx1: EvaluationContext[None] = EvaluationContext(
            user_id="user-1", groups=("beta-testers",)
        )
        ctx2: EvaluationContext[None] = EvaluationContext(
            user_id="user-2", groups=("regular",)
        )

        assert flag.is_enabled_for(ctx1) is True
        assert flag.is_enabled_for(ctx2) is False

    def test_percentage_rollout(self) -> None:
        """Test percentage rollout is deterministic."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test", name="Test", status=FlagStatus.PERCENTAGE, percentage=50.0
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-123")

        # Same user should always get same result
        result1 = flag.is_enabled_for(ctx)
        result2 = flag.is_enabled_for(ctx)
        assert result1 == result2

    def test_percentage_zero(self) -> None:
        """Test 0% rollout disables for all."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test", name="Test", status=FlagStatus.PERCENTAGE, percentage=0.0
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        assert flag.is_enabled_for(ctx) is False

    def test_percentage_hundred(self) -> None:
        """Test 100% rollout enables for all."""
        flag: FeatureFlag[None] = FeatureFlag(
            key="test", name="Test", status=FlagStatus.PERCENTAGE, percentage=100.0
        )
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        assert flag.is_enabled_for(ctx) is True


class TestFeatureFlagEvaluator:
    """Tests for FeatureFlagEvaluator."""

    def test_evaluate_not_found(self) -> None:
        """Test evaluating non-existent flag."""
        evaluator: FeatureFlagEvaluator[None] = FeatureFlagEvaluator()
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")

        result = evaluator.evaluate("unknown-flag", ctx)

        assert result.enabled is False
        assert result.reason == "FLAG_NOT_FOUND"

    def test_register_and_evaluate(self) -> None:
        """Test registering and evaluating flag."""
        evaluator: FeatureFlagEvaluator[None] = FeatureFlagEvaluator()
        flag: FeatureFlag[None] = FeatureFlag(
            key="my-flag", name="My Flag", status=FlagStatus.ENABLED
        )
        evaluator.register(flag)

        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        result = evaluator.evaluate("my-flag", ctx)

        assert result.enabled is True
        assert result.reason == "FLAG_ENABLED"

    def test_is_enabled_shortcut(self) -> None:
        """Test is_enabled shortcut method."""
        evaluator: FeatureFlagEvaluator[None] = FeatureFlagEvaluator()
        flag: FeatureFlag[None] = FeatureFlag(
            key="feature", name="Feature", status=FlagStatus.ENABLED
        )
        evaluator.register(flag)

        ctx: EvaluationContext[None] = EvaluationContext()
        assert evaluator.is_enabled("feature", ctx) is True
        assert evaluator.is_enabled("unknown", ctx) is False

    def test_evaluation_reasons(self) -> None:
        """Test different evaluation reasons."""
        evaluator: FeatureFlagEvaluator[None] = FeatureFlagEvaluator()

        # Disabled flag
        disabled_flag: FeatureFlag[None] = FeatureFlag(
            key="disabled", name="Disabled", status=FlagStatus.DISABLED
        )
        evaluator.register(disabled_flag)

        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")
        result = evaluator.evaluate("disabled", ctx)
        assert result.reason == "FLAG_DISABLED"


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_result_creation(self) -> None:
        """Test result creation."""
        result = EvaluationResult(
            flag_key="test-flag",
            enabled=True,
            reason="FLAG_ENABLED",
        )
        assert result.flag_key == "test-flag"
        assert result.enabled is True
        assert result.reason == "FLAG_ENABLED"
        assert result.variant is None
        assert result.metadata == {}

    def test_result_with_metadata(self) -> None:
        """Test result with metadata."""
        result = EvaluationResult(
            flag_key="test",
            enabled=True,
            reason="ENABLED",
            metadata={"version": "2.0"},
        )
        assert result.metadata["version"] == "2.0"

    def test_result_frozen(self) -> None:
        """Test result is immutable."""
        result = EvaluationResult(flag_key="test", enabled=True, reason="ENABLED")
        with pytest.raises(AttributeError):
            result.enabled = False  # type: ignore[misc]


class TestInMemoryFeatureFlagStore:
    """Tests for InMemoryFeatureFlagStore."""

    @pytest.mark.asyncio
    async def test_save_and_get(self) -> None:
        """Test saving and getting flag."""
        store: InMemoryFeatureFlagStore[None] = InMemoryFeatureFlagStore()
        flag: FeatureFlag[None] = FeatureFlag(key="test", name="Test")

        await store.save(flag)
        retrieved = await store.get("test")

        assert retrieved is not None
        assert retrieved.key == "test"

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        """Test getting non-existent flag."""
        store: InMemoryFeatureFlagStore[None] = InMemoryFeatureFlagStore()
        result = await store.get("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        """Test getting all flags."""
        store: InMemoryFeatureFlagStore[None] = InMemoryFeatureFlagStore()
        await store.save(FeatureFlag(key="flag1", name="Flag 1"))
        await store.save(FeatureFlag(key="flag2", name="Flag 2"))

        flags = await store.get_all()
        assert len(flags) == 2

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test deleting flag."""
        store: InMemoryFeatureFlagStore[None] = InMemoryFeatureFlagStore()
        await store.save(FeatureFlag(key="test", name="Test"))

        deleted = await store.delete("test")
        assert deleted is True

        result = await store.get("test")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test deleting non-existent flag."""
        store: InMemoryFeatureFlagStore[None] = InMemoryFeatureFlagStore()
        deleted = await store.delete("unknown")
        assert deleted is False


class TestFlagAuditLogger:
    """Tests for FlagAuditLogger."""

    def test_log_evaluation(self) -> None:
        """Test logging evaluation."""
        logger = FlagAuditLogger()
        result = EvaluationResult(flag_key="test", enabled=True, reason="ENABLED")
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")

        logger.log_evaluation(result, ctx)

        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].flag_key == "test"
        assert logs[0].user_id == "user-1"
        assert logs[0].result is True

    def test_get_logs_filtered(self) -> None:
        """Test getting filtered logs."""
        audit_logger = FlagAuditLogger()
        ctx: EvaluationContext[None] = EvaluationContext(user_id="user-1")

        audit_logger.log_evaluation(
            EvaluationResult(flag_key="flag1", enabled=True, reason="ENABLED"), ctx
        )
        audit_logger.log_evaluation(
            EvaluationResult(flag_key="flag2", enabled=False, reason="DISABLED"), ctx
        )
        audit_logger.log_evaluation(
            EvaluationResult(flag_key="flag1", enabled=True, reason="ENABLED"), ctx
        )

        flag1_logs = audit_logger.get_logs("flag1")
        assert len(flag1_logs) == 2

        all_logs = audit_logger.get_logs()
        assert len(all_logs) == 3
