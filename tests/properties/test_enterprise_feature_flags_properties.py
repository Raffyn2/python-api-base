"""Property-based tests for feature flags.

**Feature: enterprise-features-2025, Tasks 9.3, 9.5**
**Validates: Requirements 9.2, 9.7**
"""

import hashlib
from dataclasses import dataclass

from hypothesis import given, settings, strategies as st


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """Context for flag evaluation."""

    user_id: str
    tenant_id: str | None = None
    attributes: dict[str, str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.attributes is None:
            object.__setattr__(self, "attributes", {})


@dataclass(frozen=True, slots=True)
class FeatureFlag:
    """Feature flag configuration."""

    key: str
    is_enabled: bool
    rollout_percentage: int  # 0-100
    variants: tuple[str, ...] = ("control", "treatment")


class FeatureFlagService:
    """Simple feature flag service for testing."""

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def create_flag(self, flag: FeatureFlag) -> None:
        """Create a feature flag."""
        self._flags[flag.key] = flag

    def _hash_user(self, flag_key: str, user_id: str) -> int:
        """Generate consistent hash for user assignment."""
        combined = f"{flag_key}:{user_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        return int.from_bytes(hash_bytes[:4], "big") % 100

    def evaluate(
        self, flag_key: str, context: EvaluationContext, default: bool = False
    ) -> bool:
        """Evaluate a feature flag."""
        flag = self._flags.get(flag_key)
        if flag is None:
            return default

        if not flag.is_enabled:
            return False

        # Percentage rollout
        if flag.rollout_percentage == 100:
            return True
        if flag.rollout_percentage == 0:
            return False

        user_hash = self._hash_user(flag_key, context.user_id)
        return user_hash < flag.rollout_percentage

    def get_variant(
        self, flag_key: str, context: EvaluationContext, default: str = "control"
    ) -> str:
        """Get variant assignment for user."""
        flag = self._flags.get(flag_key)
        if flag is None or not flag.is_enabled:
            return default

        if not flag.variants:
            return default

        # Consistent variant assignment
        user_hash = self._hash_user(flag_key, context.user_id)
        variant_index = user_hash % len(flag.variants)
        return flag.variants[variant_index]


# Strategies
flag_keys = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=30,
)
user_ids = st.uuids().map(str)
percentages = st.integers(min_value=0, max_value=100)


class TestPercentageRollout:
    """**Feature: enterprise-features-2025, Property 19: Feature Flag Percentage Rollout**
    **Validates: Requirements 9.2**
    """

    @given(
        flag_key=flag_keys,
        percentage=percentages,
        user_ids_list=st.lists(user_ids, min_size=100, max_size=200),
    )
    @settings(max_examples=20)
    def test_percentage_rollout_within_tolerance(
        self, flag_key: str, percentage: int, user_ids_list: list[str]
    ) -> None:
        """Percentage rollout is within statistical tolerance."""
        service = FeatureFlagService()
        flag = FeatureFlag(
            key=flag_key,
            is_enabled=True,
            rollout_percentage=percentage,
        )
        service.create_flag(flag)

        enabled_count = 0
        for user_id in user_ids_list:
            context = EvaluationContext(user_id=user_id)
            if service.evaluate(flag_key, context):
                enabled_count += 1

        actual_percentage = (enabled_count / len(user_ids_list)) * 100

        # Allow 15% tolerance for statistical variance
        tolerance = 15
        if percentage == 0:
            assert enabled_count == 0
        elif percentage == 100:
            assert enabled_count == len(user_ids_list)
        else:
            assert abs(actual_percentage - percentage) <= tolerance

    @given(flag_key=flag_keys, user_id=user_ids)
    @settings(max_examples=50)
    def test_zero_percentage_always_disabled(self, flag_key: str, user_id: str) -> None:
        """0% rollout is always disabled."""
        service = FeatureFlagService()
        flag = FeatureFlag(key=flag_key, is_enabled=True, rollout_percentage=0)
        service.create_flag(flag)

        context = EvaluationContext(user_id=user_id)
        assert not service.evaluate(flag_key, context)

    @given(flag_key=flag_keys, user_id=user_ids)
    @settings(max_examples=50)
    def test_hundred_percentage_always_enabled(
        self, flag_key: str, user_id: str
    ) -> None:
        """100% rollout is always enabled."""
        service = FeatureFlagService()
        flag = FeatureFlag(key=flag_key, is_enabled=True, rollout_percentage=100)
        service.create_flag(flag)

        context = EvaluationContext(user_id=user_id)
        assert service.evaluate(flag_key, context)


class TestVariantConsistency:
    """**Feature: enterprise-features-2025, Property 20: Feature Flag Variant Consistency**
    **Validates: Requirements 9.7**
    """

    @given(
        flag_key=flag_keys,
        user_id=user_ids,
        variants=st.lists(
            st.text(min_size=1, max_size=20),
            min_size=2,
            max_size=5,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_same_user_gets_same_variant(
        self, flag_key: str, user_id: str, variants: list[str]
    ) -> None:
        """Same user always gets the same variant."""
        service = FeatureFlagService()
        flag = FeatureFlag(
            key=flag_key,
            is_enabled=True,
            rollout_percentage=100,
            variants=tuple(variants),
        )
        service.create_flag(flag)

        context = EvaluationContext(user_id=user_id)

        # Call multiple times
        results = [service.get_variant(flag_key, context) for _ in range(10)]

        # All results should be the same
        assert len(set(results)) == 1
        assert results[0] in variants

    @given(
        flag_key=flag_keys,
        user_ids_list=st.lists(user_ids, min_size=50, max_size=100, unique=True),
    )
    @settings(max_examples=20)
    def test_variants_distributed_across_users(
        self, flag_key: str, user_ids_list: list[str]
    ) -> None:
        """Variants are distributed across users."""
        variants = ("control", "treatment")
        service = FeatureFlagService()
        flag = FeatureFlag(
            key=flag_key,
            is_enabled=True,
            rollout_percentage=100,
            variants=variants,
        )
        service.create_flag(flag)

        variant_counts: dict[str, int] = dict.fromkeys(variants, 0)
        for user_id in user_ids_list:
            context = EvaluationContext(user_id=user_id)
            variant = service.get_variant(flag_key, context)
            variant_counts[variant] += 1

        # Both variants should have some users (with enough samples)
        for variant in variants:
            assert variant_counts[variant] > 0

    @given(flag_key=flag_keys, user_id=user_ids)
    @settings(max_examples=50)
    def test_disabled_flag_returns_default_variant(
        self, flag_key: str, user_id: str
    ) -> None:
        """Disabled flag returns default variant."""
        service = FeatureFlagService()
        flag = FeatureFlag(
            key=flag_key,
            is_enabled=False,
            rollout_percentage=100,
            variants=("a", "b"),
        )
        service.create_flag(flag)

        context = EvaluationContext(user_id=user_id)
        variant = service.get_variant(flag_key, context, default="control")

        assert variant == "control"


class TestFlagEvaluation:
    """Additional flag evaluation tests."""

    @given(flag_key=flag_keys, user_id=user_ids)
    @settings(max_examples=50)
    def test_nonexistent_flag_returns_default(
        self, flag_key: str, user_id: str
    ) -> None:
        """Non-existent flag returns default value."""
        service = FeatureFlagService()
        context = EvaluationContext(user_id=user_id)

        assert not service.evaluate(flag_key, context, default=False)
        assert service.evaluate(flag_key, context, default=True)

    @given(flag_key=flag_keys, user_id=user_ids)
    @settings(max_examples=50)
    def test_disabled_flag_always_false(self, flag_key: str, user_id: str) -> None:
        """Disabled flag always returns False."""
        service = FeatureFlagService()
        flag = FeatureFlag(key=flag_key, is_enabled=False, rollout_percentage=100)
        service.create_flag(flag)

        context = EvaluationContext(user_id=user_id)
        assert not service.evaluate(flag_key, context)
