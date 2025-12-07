"""Tests for feature flags config module."""

from datetime import UTC, datetime

import pytest

from application.services.feature_flags.config.config import FlagConfig
from application.services.feature_flags.core.enums import FlagStatus


class TestFlagConfig:
    """Tests for FlagConfig dataclass."""

    def test_minimal_config(self) -> None:
        config = FlagConfig(key="feature-x")
        assert config.key == "feature-x"
        assert config.name == ""
        assert config.description == ""
        assert config.status == FlagStatus.DISABLED

    def test_with_name_and_description(self) -> None:
        config = FlagConfig(
            key="feature-x",
            name="Feature X",
            description="A new feature",
        )
        assert config.name == "Feature X"
        assert config.description == "A new feature"

    def test_with_status(self) -> None:
        config = FlagConfig(key="feature-x", status=FlagStatus.ENABLED)
        assert config.status == FlagStatus.ENABLED

    def test_default_values(self) -> None:
        config = FlagConfig(key="feature-x")
        assert config.default_value is False
        assert config.enabled_value is True

    def test_custom_values(self) -> None:
        config = FlagConfig(
            key="feature-x",
            default_value="off",
            enabled_value="on",
        )
        assert config.default_value == "off"
        assert config.enabled_value == "on"

    def test_percentage(self) -> None:
        config = FlagConfig(key="feature-x", percentage=50.0)
        assert config.percentage == 50.0

    def test_user_ids(self) -> None:
        config = FlagConfig(key="feature-x", user_ids=["user-1", "user-2"])
        assert config.user_ids == ["user-1", "user-2"]

    def test_groups(self) -> None:
        config = FlagConfig(key="feature-x", groups=["beta", "internal"])
        assert config.groups == ["beta", "internal"]

    def test_timestamps_auto_generated(self) -> None:
        before = datetime.now(UTC)
        config = FlagConfig(key="feature-x")
        after = datetime.now(UTC)
        assert before <= config.created_at <= after
        assert before <= config.updated_at <= after

    def test_user_ids_default_is_mutable(self) -> None:
        config1 = FlagConfig(key="feature-1")
        config2 = FlagConfig(key="feature-2")
        config1.user_ids.append("user-1")
        assert "user-1" not in config2.user_ids

    def test_groups_default_is_mutable(self) -> None:
        config1 = FlagConfig(key="feature-1")
        config2 = FlagConfig(key="feature-2")
        config1.groups.append("group-1")
        assert "group-1" not in config2.groups

    def test_full_config(self) -> None:
        config = FlagConfig(
            key="premium-feature",
            name="Premium Feature",
            description="Available for premium users",
            status=FlagStatus.TARGETED,
            default_value=False,
            enabled_value=True,
            percentage=0.0,
            user_ids=["vip-1", "vip-2"],
            groups=["premium", "enterprise"],
        )
        assert config.key == "premium-feature"
        assert config.status == FlagStatus.TARGETED
        assert len(config.user_ids) == 2
        assert len(config.groups) == 2
