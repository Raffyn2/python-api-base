"""Unit tests for FeatureFlagService.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.4**
"""

import pytest

from application.services.feature_flags.config import FlagConfig
from application.services.feature_flags.core import FlagStatus
from application.services.feature_flags.models import EvaluationContext
from application.services.feature_flags.service.service import (
    FeatureFlagService,
    FlagEvaluation,
    create_flag,
)


class TestFlagEvaluation:
    """Tests for FlagEvaluation model."""

    def test_create_evaluation(self) -> None:
        """Should create evaluation with all fields."""
        evaluation = FlagEvaluation(
            flag_key="test_flag",
            value=True,
            reason="Enabled",
            is_default=False,
        )

        assert evaluation.flag_key == "test_flag"
        assert evaluation.value is True
        assert evaluation.reason == "Enabled"
        assert evaluation.is_default is False

    def test_default_is_default(self) -> None:
        """is_default should default to False."""
        evaluation = FlagEvaluation(
            flag_key="test",
            value=False,
            reason="Test",
        )

        assert evaluation.is_default is False


class TestFeatureFlagService:
    """Tests for FeatureFlagService."""

    @pytest.fixture
    def service(self) -> FeatureFlagService:
        """Create service instance."""
        return FeatureFlagService(seed=42)

    @pytest.fixture
    def sample_flag(self) -> FlagConfig:
        """Create sample flag config."""
        return FlagConfig(
            key="test_feature",
            name="Test Feature",
            status=FlagStatus.ENABLED,
        )

    def test_register_flag(self, service: FeatureFlagService, sample_flag: FlagConfig) -> None:
        """Should register a flag."""
        service.register_flag(sample_flag)

        assert service.get_flag("test_feature") == sample_flag

    def test_unregister_flag(self, service: FeatureFlagService, sample_flag: FlagConfig) -> None:
        """Should unregister a flag."""
        service.register_flag(sample_flag)

        result = service.unregister_flag("test_feature")

        assert result is True
        assert service.get_flag("test_feature") is None

    def test_unregister_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.unregister_flag("nonexistent")

        assert result is False

    def test_get_flag(self, service: FeatureFlagService, sample_flag: FlagConfig) -> None:
        """Should get registered flag."""
        service.register_flag(sample_flag)

        flag = service.get_flag("test_feature")

        assert flag == sample_flag

    def test_get_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return None for nonexistent flag."""
        flag = service.get_flag("nonexistent")

        assert flag is None

    def test_list_flags(self, service: FeatureFlagService) -> None:
        """Should list all registered flags."""
        flag1 = FlagConfig(key="flag1", name="Flag 1", status=FlagStatus.ENABLED)
        flag2 = FlagConfig(key="flag2", name="Flag 2", status=FlagStatus.DISABLED)

        service.register_flag(flag1)
        service.register_flag(flag2)

        flags = service.list_flags()

        assert len(flags) == 2
        assert flag1 in flags
        assert flag2 in flags

    def test_is_enabled_true(self, service: FeatureFlagService) -> None:
        """Should return True for enabled flag."""
        flag = FlagConfig(key="enabled", name="Enabled", status=FlagStatus.ENABLED)
        service.register_flag(flag)

        result = service.is_enabled("enabled")

        assert result is True

    def test_is_enabled_false(self, service: FeatureFlagService) -> None:
        """Should return False for disabled flag."""
        flag = FlagConfig(key="disabled", name="Disabled", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        result = service.is_enabled("disabled")

        assert result is False

    def test_is_enabled_nonexistent(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.is_enabled("nonexistent")

        assert result is False

    def test_evaluate_enabled_flag(self, service: FeatureFlagService) -> None:
        """Should evaluate enabled flag."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.ENABLED)
        service.register_flag(flag)

        evaluation = service.evaluate("test")

        assert evaluation.flag_key == "test"
        assert evaluation.value is True

    def test_evaluate_disabled_flag(self, service: FeatureFlagService) -> None:
        """Should evaluate disabled flag."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        evaluation = service.evaluate("test")

        assert evaluation.flag_key == "test"
        assert evaluation.value is False

    def test_evaluate_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return default for nonexistent flag."""
        evaluation = service.evaluate("nonexistent")

        assert evaluation.flag_key == "nonexistent"
        assert evaluation.value is False
        assert evaluation.is_default is True
        assert "not found" in evaluation.reason.lower()

    def test_evaluate_with_context(self, service: FeatureFlagService) -> None:
        """Should evaluate with context."""
        flag = FlagConfig(
            key="targeted",
            name="Targeted",
            status=FlagStatus.TARGETED,
            user_ids=["user-123"],
        )
        service.register_flag(flag)

        context = EvaluationContext(user_id="user-123")
        evaluation = service.evaluate("targeted", context)

        assert evaluation.value is True

    def test_enable_flag(self, service: FeatureFlagService) -> None:
        """Should enable a flag."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        result = service.enable_flag("test")

        assert result is True
        assert service.get_flag("test").status == FlagStatus.ENABLED

    def test_enable_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.enable_flag("nonexistent")

        assert result is False

    def test_disable_flag(self, service: FeatureFlagService) -> None:
        """Should disable a flag."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.ENABLED)
        service.register_flag(flag)

        result = service.disable_flag("test")

        assert result is True
        assert service.get_flag("test").status == FlagStatus.DISABLED

    def test_disable_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.disable_flag("nonexistent")

        assert result is False

    def test_set_percentage(self, service: FeatureFlagService) -> None:
        """Should set percentage rollout."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        result = service.set_percentage("test", 50.0)

        assert result is True
        flag = service.get_flag("test")
        assert flag.status == FlagStatus.PERCENTAGE
        assert flag.percentage == 50.0

    def test_set_percentage_clamps_values(self, service: FeatureFlagService) -> None:
        """Should clamp percentage to 0-100."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        service.set_percentage("test", 150.0)
        assert service.get_flag("test").percentage == 100.0

        service.set_percentage("test", -10.0)
        assert service.get_flag("test").percentage == 0.0

    def test_set_percentage_nonexistent(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.set_percentage("nonexistent", 50.0)

        assert result is False

    def test_add_user_target(self, service: FeatureFlagService) -> None:
        """Should add user to targeting."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED)
        service.register_flag(flag)

        result = service.add_user_target("test", "user-123")

        assert result is True
        flag = service.get_flag("test")
        assert "user-123" in flag.user_ids
        assert flag.status == FlagStatus.TARGETED

    def test_add_user_target_duplicate(self, service: FeatureFlagService) -> None:
        """Should not add duplicate user."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.DISABLED, user_ids=["user-123"])
        service.register_flag(flag)

        service.add_user_target("test", "user-123")

        assert service.get_flag("test").user_ids.count("user-123") == 1

    def test_add_user_target_nonexistent(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.add_user_target("nonexistent", "user-123")

        assert result is False

    def test_remove_user_target(self, service: FeatureFlagService) -> None:
        """Should remove user from targeting."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.TARGETED, user_ids=["user-123"])
        service.register_flag(flag)

        result = service.remove_user_target("test", "user-123")

        assert result is True
        assert "user-123" not in service.get_flag("test").user_ids

    def test_remove_user_target_not_found(self, service: FeatureFlagService) -> None:
        """Should return False when user not in list."""
        flag = FlagConfig(key="test", name="Test", status=FlagStatus.TARGETED, user_ids=[])
        service.register_flag(flag)

        result = service.remove_user_target("test", "user-123")

        assert result is False

    def test_remove_user_target_nonexistent_flag(self, service: FeatureFlagService) -> None:
        """Should return False for nonexistent flag."""
        result = service.remove_user_target("nonexistent", "user-123")

        assert result is False


class TestCreateFlag:
    """Tests for create_flag helper function."""

    def test_create_disabled_flag(self) -> None:
        """Should create disabled flag by default."""
        flag = create_flag("test_flag")

        assert flag.key == "test_flag"
        assert flag.name == "test_flag"
        assert flag.status == FlagStatus.DISABLED

    def test_create_enabled_flag(self) -> None:
        """Should create enabled flag."""
        flag = create_flag("test_flag", enabled=True)

        assert flag.status == FlagStatus.ENABLED

    def test_create_with_name(self) -> None:
        """Should use provided name."""
        flag = create_flag("test_flag", name="Test Flag")

        assert flag.name == "Test Flag"

    def test_create_with_percentage(self) -> None:
        """Should create percentage flag."""
        flag = create_flag("test_flag", percentage=50.0)

        assert flag.status == FlagStatus.PERCENTAGE
        assert flag.percentage == 50.0
