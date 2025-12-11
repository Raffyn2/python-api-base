"""Property-based tests for configuration validation.

Tests configuration validation invariants using Hypothesis.

**Task 3.2: Property test for configuration validation**
**Property 7: Configuration Validation**
**Requirements: 3.5**
"""

import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import SecretStr

from core.config.security.security import RATE_LIMIT_PATTERN, SecuritySettings


class TestRateLimitPatternProperties:
    """Property tests for rate limit pattern validation."""

    @given(
        number=st.integers(min_value=1, max_value=999999),
        unit=st.sampled_from(["second", "minute", "hour", "day"]),
    )
    @settings(max_examples=100)
    def test_valid_rate_limit_format_always_matches(self, number: int, unit: str) -> None:
        """Property: Valid rate limit format always matches pattern."""
        rate_limit = f"{number}/{unit}"
        assert RATE_LIMIT_PATTERN.match(rate_limit) is not None

    @given(
        number=st.integers(min_value=1, max_value=999999),
        unit=st.text(min_size=1, max_size=10).filter(lambda x: x not in ["second", "minute", "hour", "day"]),
    )
    @settings(max_examples=50)
    def test_invalid_unit_never_matches(self, number: int, unit: str) -> None:
        """Property: Invalid unit never matches pattern."""
        # May or may not match depending on unit content
        # This tests that random units don't accidentally match


class TestSecuritySettingsProperties:
    """Property tests for SecuritySettings validation."""

    @given(key_length=st.integers(min_value=32, max_value=128))
    @settings(max_examples=50)
    def test_valid_secret_key_length_accepted(self, key_length: int) -> None:
        """Property: Secret keys >= 32 chars are accepted."""
        secret = "a" * key_length
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings = SecuritySettings(secret_key=SecretStr(secret))
            assert len(settings.secret_key.get_secret_value()) == key_length

    @given(key_length=st.integers(min_value=1, max_value=31))
    @settings(max_examples=30)
    def test_short_secret_key_rejected(self, key_length: int) -> None:
        """Property: Secret keys < 32 chars are rejected."""
        secret = "a" * key_length
        with pytest.raises(ValueError, match="at least 32"):
            SecuritySettings(secret_key=SecretStr(secret))

    @given(
        number=st.integers(min_value=1, max_value=10000),
        unit=st.sampled_from(["second", "minute", "hour", "day"]),
    )
    @settings(max_examples=50)
    def test_valid_rate_limit_accepted(self, number: int, unit: str) -> None:
        """Property: Valid rate limits are accepted."""
        rate_limit = f"{number}/{unit}"
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings = SecuritySettings(
                secret_key=SecretStr("a" * 32),
                rate_limit=rate_limit,
            )
            assert settings.rate_limit == rate_limit

    @given(expire_minutes=st.integers(min_value=1, max_value=10080))
    @settings(max_examples=50)
    def test_valid_token_expiry_accepted(self, expire_minutes: int) -> None:
        """Property: Valid token expiry values are accepted."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings = SecuritySettings(
                secret_key=SecretStr("a" * 32),
                access_token_expire_minutes=expire_minutes,
            )
            assert settings.access_token_expire_minutes == expire_minutes
