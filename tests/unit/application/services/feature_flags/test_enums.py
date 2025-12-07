"""Tests for feature flags enums module."""

import pytest

from application.services.feature_flags.core.enums import FlagStatus, RolloutStrategy


class TestFlagStatus:
    """Tests for FlagStatus enum."""

    def test_enabled_value(self) -> None:
        assert FlagStatus.ENABLED.value == "enabled"

    def test_disabled_value(self) -> None:
        assert FlagStatus.DISABLED.value == "disabled"

    def test_percentage_value(self) -> None:
        assert FlagStatus.PERCENTAGE.value == "percentage"

    def test_targeted_value(self) -> None:
        assert FlagStatus.TARGETED.value == "targeted"

    def test_is_str_enum(self) -> None:
        assert isinstance(FlagStatus.ENABLED, str)
        assert FlagStatus.ENABLED == "enabled"

    def test_all_values(self) -> None:
        values = [s.value for s in FlagStatus]
        assert "enabled" in values
        assert "disabled" in values
        assert "percentage" in values
        assert "targeted" in values


class TestRolloutStrategy:
    """Tests for RolloutStrategy enum."""

    def test_all_value(self) -> None:
        assert RolloutStrategy.ALL.value == "all"

    def test_none_value(self) -> None:
        assert RolloutStrategy.NONE.value == "none"

    def test_percentage_value(self) -> None:
        assert RolloutStrategy.PERCENTAGE.value == "percentage"

    def test_user_ids_value(self) -> None:
        assert RolloutStrategy.USER_IDS.value == "user_ids"

    def test_groups_value(self) -> None:
        assert RolloutStrategy.GROUPS.value == "groups"

    def test_custom_value(self) -> None:
        assert RolloutStrategy.CUSTOM.value == "custom"

    def test_is_str_enum(self) -> None:
        assert isinstance(RolloutStrategy.ALL, str)
        assert RolloutStrategy.ALL == "all"

    def test_all_values(self) -> None:
        values = [s.value for s in RolloutStrategy]
        assert len(values) == 6
