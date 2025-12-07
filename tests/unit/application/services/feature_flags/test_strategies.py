"""Unit tests for feature flag evaluation strategies.

Tests DisabledStrategy, EnabledStrategy, and other evaluation strategies.
"""

import pytest

from application.services.feature_flags.config import FlagConfig
from application.services.feature_flags.core import FlagStatus
from application.services.feature_flags.core.base import FlagEvaluationResult
from application.services.feature_flags.models import EvaluationContext
from application.services.feature_flags.strategies.status import (
    DisabledStrategy,
    EnabledStrategy,
)


class TestFlagEvaluationResult:
    """Tests for FlagEvaluationResult class."""

    def test_no_match(self) -> None:
        """Test no_match factory method."""
        result = FlagEvaluationResult.no_match()

        assert result.matched is False
        assert result.value is None
        assert result.reason == "No match"

    def test_match(self) -> None:
        """Test match factory method."""
        result = FlagEvaluationResult.match(value=True, reason="Test reason")

        assert result.matched is True
        assert result.value is True
        assert result.reason == "Test reason"

    def test_match_with_complex_value(self) -> None:
        """Test match with complex value."""
        value = {"feature": "enabled", "variant": "A"}
        result = FlagEvaluationResult.match(value=value, reason="Complex value")

        assert result.matched is True
        assert result.value == value


class TestDisabledStrategy:
    """Tests for DisabledStrategy."""

    @pytest.fixture
    def strategy(self) -> DisabledStrategy:
        """Create strategy instance."""
        return DisabledStrategy()

    @pytest.fixture
    def context(self) -> EvaluationContext:
        """Create evaluation context."""
        return EvaluationContext(user_id="user-1")

    def test_priority(self, strategy: DisabledStrategy) -> None:
        """Test strategy has highest priority."""
        assert strategy.priority == 0

    def test_evaluate_disabled_flag(
        self, strategy: DisabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns default value for disabled flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.DISABLED,
            default_value=False,
            enabled_value=True,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is True
        assert result.value is False
        assert "disabled" in result.reason.lower()


    def test_evaluate_enabled_flag_no_match(
        self, strategy: DisabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns no match for enabled flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.ENABLED,
            default_value=False,
            enabled_value=True,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is False

    def test_evaluate_percentage_flag_no_match(
        self, strategy: DisabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns no match for percentage flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.PERCENTAGE,
            default_value=False,
            enabled_value=True,
            percentage=50.0,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is False


class TestEnabledStrategy:
    """Tests for EnabledStrategy."""

    @pytest.fixture
    def strategy(self) -> EnabledStrategy:
        """Create strategy instance."""
        return EnabledStrategy()

    @pytest.fixture
    def context(self) -> EvaluationContext:
        """Create evaluation context."""
        return EvaluationContext(user_id="user-1")

    def test_priority(self, strategy: EnabledStrategy) -> None:
        """Test strategy has second highest priority."""
        assert strategy.priority == 1

    def test_evaluate_enabled_flag(
        self, strategy: EnabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns enabled value for enabled flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.ENABLED,
            default_value=False,
            enabled_value=True,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is True
        assert result.value is True
        assert "enabled" in result.reason.lower()

    def test_evaluate_disabled_flag_no_match(
        self, strategy: EnabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns no match for disabled flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.DISABLED,
            default_value=False,
            enabled_value=True,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is False

    def test_evaluate_percentage_flag_no_match(
        self, strategy: EnabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns no match for percentage flag."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.PERCENTAGE,
            default_value=False,
            enabled_value=True,
            percentage=50.0,
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is False

    def test_evaluate_with_custom_enabled_value(
        self, strategy: EnabledStrategy, context: EvaluationContext
    ) -> None:
        """Test evaluation returns custom enabled value."""
        flag = FlagConfig(
            key="test-flag",
            status=FlagStatus.ENABLED,
            default_value="default",
            enabled_value={"variant": "A", "config": {"limit": 100}},
        )

        result = strategy.evaluate(flag, context)

        assert result.matched is True
        assert result.value == {"variant": "A", "config": {"limit": 100}}


class TestFlagConfig:
    """Tests for FlagConfig dataclass."""

    def test_default_values(self) -> None:
        """Test FlagConfig default values."""
        flag = FlagConfig(key="test-flag")

        assert flag.key == "test-flag"
        assert flag.name == ""
        assert flag.description == ""
        assert flag.status == FlagStatus.DISABLED
        assert flag.default_value is False
        assert flag.enabled_value is True
        assert flag.percentage == 0.0
        assert flag.user_ids == []
        assert flag.groups == []

    def test_custom_values(self) -> None:
        """Test FlagConfig with custom values."""
        flag = FlagConfig(
            key="feature-x",
            name="Feature X",
            description="New feature X",
            status=FlagStatus.PERCENTAGE,
            default_value=False,
            enabled_value=True,
            percentage=25.0,
            user_ids=["user-1", "user-2"],
            groups=["beta-testers"],
        )

        assert flag.key == "feature-x"
        assert flag.name == "Feature X"
        assert flag.status == FlagStatus.PERCENTAGE
        assert flag.percentage == 25.0
        assert len(flag.user_ids) == 2
        assert "beta-testers" in flag.groups


class TestEvaluationContext:
    """Tests for EvaluationContext dataclass."""

    def test_default_values(self) -> None:
        """Test EvaluationContext default values."""
        context = EvaluationContext()

        assert context.user_id is None
        assert context.groups == []
        assert context.attributes == {}

    def test_with_user_id(self) -> None:
        """Test EvaluationContext with user ID."""
        context = EvaluationContext(user_id="user-123")

        assert context.user_id == "user-123"

    def test_with_groups(self) -> None:
        """Test EvaluationContext with groups."""
        context = EvaluationContext(
            user_id="user-123",
            groups=["admin", "beta-testers"],
        )

        assert len(context.groups) == 2
        assert "admin" in context.groups

    def test_with_attributes(self) -> None:
        """Test EvaluationContext with attributes."""
        context = EvaluationContext(
            user_id="user-123",
            attributes={"country": "BR", "plan": "premium"},
        )

        assert context.attributes["country"] == "BR"
        assert context.attributes["plan"] == "premium"
