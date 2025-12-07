"""Property-based tests for configuration validation.

**Feature: test-coverage-80-percent, Property 8: Configuration Validation**
**Validates: Requirements 2.1**
"""

import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import SecretStr, ValidationError

from core.config import (
    DatabaseSettings,
    ObservabilitySettings,
    SecuritySettings,
)


class TestConfigurationValidationProperties:
    """Property-based tests for configuration validation."""

    @given(
        pool_size=st.integers(min_value=1, max_value=100),
        max_overflow=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=50)
    def test_database_valid_pool_settings(
        self, pool_size: int, max_overflow: int
    ) -> None:
        """
        **Feature: test-coverage-80-percent, Property 8: Configuration Validation**

        For any valid pool_size and max_overflow within bounds,
        DatabaseSettings SHALL accept the configuration.
        """
        settings_obj = DatabaseSettings(
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        assert settings_obj.pool_size == pool_size
        assert settings_obj.max_overflow == max_overflow

    @given(pool_size=st.integers(max_value=0) | st.integers(min_value=101))
    @settings(max_examples=30)
    def test_database_invalid_pool_size_rejected(self, pool_size: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 8: Configuration Validation**

        For any pool_size outside valid bounds,
        DatabaseSettings SHALL reject the configuration.
        """
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_size=pool_size)

    @given(
        secret_key=st.text(min_size=32, max_size=64, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        ))
    )
    @settings(max_examples=50)
    def test_security_valid_secret_key(self, secret_key: str) -> None:
        """
        **Feature: test-coverage-80-percent, Property 8: Configuration Validation**

        For any secret_key with at least 32 characters,
        SecuritySettings SHALL accept the configuration.
        """
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings_obj = SecuritySettings(secret_key=SecretStr(secret_key))
            assert len(settings_obj.secret_key.get_secret_value()) >= 32

    @given(
        number=st.integers(min_value=1, max_value=1000),
        unit=st.sampled_from(["second", "minute", "hour", "day"]),
    )
    @settings(max_examples=50)
    def test_security_valid_rate_limit_format(self, number: int, unit: str) -> None:
        """
        **Feature: test-coverage-80-percent, Property 8: Configuration Validation**

        For any valid rate limit format (number/unit),
        SecuritySettings SHALL accept the configuration.
        """
        rate_limit = f"{number}/{unit}"
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings_obj = SecuritySettings(
                secret_key=SecretStr("a" * 32),
                rate_limit=rate_limit,
            )
            assert settings_obj.rate_limit == rate_limit

    @given(
        log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        log_format=st.sampled_from(["json", "console"]),
    )
    @settings(max_examples=30)
    def test_observability_valid_log_settings(
        self, log_level: str, log_format: str
    ) -> None:
        """
        **Feature: test-coverage-80-percent, Property 8: Configuration Validation**

        For any valid log_level and log_format,
        ObservabilitySettings SHALL accept the configuration.
        """
        settings_obj = ObservabilitySettings(
            log_level=log_level,
            log_format=log_format,
        )
        assert settings_obj.log_level == log_level
        assert settings_obj.log_format == log_format
