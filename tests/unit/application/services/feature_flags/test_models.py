"""Tests for feature flags models."""

import pytest

from application.services.feature_flags.models.models import EvaluationContext


class TestEvaluationContext:
    """Tests for EvaluationContext dataclass."""

    def test_default_values(self) -> None:
        ctx = EvaluationContext()
        assert ctx.user_id is None
        assert ctx.groups == []
        assert ctx.attributes == {}

    def test_with_user_id(self) -> None:
        ctx = EvaluationContext(user_id="user-123")
        assert ctx.user_id == "user-123"

    def test_with_groups(self) -> None:
        ctx = EvaluationContext(groups=["admin", "beta"])
        assert ctx.groups == ["admin", "beta"]

    def test_with_attributes(self) -> None:
        ctx = EvaluationContext(attributes={"plan": "premium", "country": "US"})
        assert ctx.attributes["plan"] == "premium"
        assert ctx.attributes["country"] == "US"

    def test_with_all_fields(self) -> None:
        ctx = EvaluationContext(
            user_id="user-456",
            groups=["testers"],
            attributes={"version": "2.0"},
        )
        assert ctx.user_id == "user-456"
        assert ctx.groups == ["testers"]
        assert ctx.attributes["version"] == "2.0"

    def test_groups_default_is_mutable(self) -> None:
        ctx1 = EvaluationContext()
        ctx2 = EvaluationContext()
        ctx1.groups.append("test")
        # Each instance should have its own list
        assert "test" not in ctx2.groups

    def test_attributes_default_is_mutable(self) -> None:
        ctx1 = EvaluationContext()
        ctx2 = EvaluationContext()
        ctx1.attributes["key"] = "value"
        # Each instance should have its own dict
        assert "key" not in ctx2.attributes
