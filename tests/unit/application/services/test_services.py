"""Unit tests for application services.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 7.1, 7.2, 7.3**
"""

from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings, strategies as st

from application.services.feature_flags import (
    DisabledStrategy,
    EnabledStrategy,
    EvaluationContext,
    FeatureFlagService,
    FlagConfig,
    FlagStatus,
)
from application.services.file_upload import (
    FileValidationConfig,
    UploadError,
    validate_file,
)
from application.services.multitenancy import (
    TenantContext,
    TenantMiddleware,
    get_current_tenant,
    require_tenant,
    set_current_tenant,
)


class TestFeatureFlagService:
    """Tests for FeatureFlagService class."""

    @pytest.fixture()
    def service(self) -> FeatureFlagService:
        """Create feature flag service."""
        return FeatureFlagService()

    def test_register_flag(self, service: FeatureFlagService) -> None:
        """Test registering a feature flag."""
        config = FlagConfig(
            key="test_flag",
            name="Test Flag",
            description="Test flag",
            status=FlagStatus.ENABLED,
        )
        service.register_flag(config)

        assert "test_flag" in service._flags

    def test_is_enabled_returns_true_for_enabled_flag(self, service: FeatureFlagService) -> None:
        """Test is_enabled returns True for enabled flag."""
        config = FlagConfig(
            key="enabled_flag",
            name="Enabled Flag",
            status=FlagStatus.ENABLED,
        )
        service.register_flag(config)

        assert service.is_enabled("enabled_flag") is True

    def test_is_enabled_returns_false_for_disabled_flag(self, service: FeatureFlagService) -> None:
        """Test is_enabled returns False for disabled flag."""
        config = FlagConfig(
            key="disabled_flag",
            name="Disabled Flag",
            status=FlagStatus.DISABLED,
        )
        service.register_flag(config)

        assert service.is_enabled("disabled_flag") is False

    def test_is_enabled_returns_false_for_unknown_flag(self, service: FeatureFlagService) -> None:
        """Test is_enabled returns False for unknown flag."""
        assert service.is_enabled("unknown_flag") is False

    def test_list_flags(self, service: FeatureFlagService) -> None:
        """Test listing all registered flags."""
        config1 = FlagConfig(key="flag1", name="Flag 1", status=FlagStatus.ENABLED)
        config2 = FlagConfig(key="flag2", name="Flag 2", status=FlagStatus.DISABLED)
        service.register_flag(config1)
        service.register_flag(config2)

        flags = service.list_flags()

        assert len(flags) == 2


class TestFeatureFlagStrategies:
    """Tests for feature flag rollout strategies."""

    def test_enabled_strategy_returns_match_for_enabled_flag(self) -> None:
        """Test EnabledStrategy returns match for enabled flag."""
        strategy = EnabledStrategy()
        flag = FlagConfig(key="test", status=FlagStatus.ENABLED)
        context = EvaluationContext(user_id="any_user")

        result = strategy.evaluate(flag, context)
        assert result.matched is True

    def test_disabled_strategy_returns_match_for_disabled_flag(self) -> None:
        """Test DisabledStrategy returns match for disabled flag."""
        strategy = DisabledStrategy()
        flag = FlagConfig(key="test", status=FlagStatus.DISABLED)
        context = EvaluationContext(user_id="any_user")

        result = strategy.evaluate(flag, context)
        assert result.matched is True


class TestFileValidation:
    """Tests for file validation functions."""

    @pytest.fixture()
    def config(self) -> FileValidationConfig:
        """Create file validation config."""
        return FileValidationConfig(
            max_size_bytes=1024 * 1024,  # 1MB
            allowed_extensions=frozenset({".jpg", ".png", ".pdf"}),
            allowed_types=frozenset({"image/jpeg", "image/png", "application/pdf"}),
        )

    def test_validate_file_valid(self, config: FileValidationConfig) -> None:
        """Test valid file passes validation."""
        # JPEG magic bytes
        content = b"\xff\xd8\xff" + b"x" * 100

        result = validate_file("test.jpg", content, "image/jpeg", config)

        assert result.is_ok()

    def test_validate_file_size_exceeds_limit(self, config: FileValidationConfig) -> None:
        """Test file exceeding size limit fails validation."""
        content = b"x" * (2 * 1024 * 1024)  # 2MB

        result = validate_file("test.jpg", content, "image/jpeg", config)

        assert result.is_err()
        assert result.error == UploadError.FILE_TOO_LARGE

    def test_validate_file_invalid_extension(self, config: FileValidationConfig) -> None:
        """Test invalid extension fails validation."""
        content = b"test content"

        result = validate_file("script.exe", content, "application/octet-stream", config)

        assert result.is_err()

    def test_validate_file_invalid_content_type(self, config: FileValidationConfig) -> None:
        """Test invalid content type fails validation."""
        content = b"test content"

        result = validate_file("test.txt", content, "text/plain", config)

        assert result.is_err()
        assert result.error == UploadError.INVALID_TYPE


class TestTenantContext:
    """Tests for TenantContext class.

    **Feature: test-coverage-80-percent-v3**
    **Validates: Requirements 7.3**
    """

    def test_set_and_get_current_tenant(self) -> None:
        """Test setting and getting current tenant."""
        set_current_tenant("tenant_123")
        assert get_current_tenant() == "tenant_123"
        set_current_tenant(None)

    def test_tenant_context_sync(self) -> None:
        """Test TenantContext as sync context manager."""
        set_current_tenant(None)
        assert get_current_tenant() is None

        with TenantContext("tenant_abc"):
            assert get_current_tenant() == "tenant_abc"

        assert get_current_tenant() is None

    def test_tenant_context_restores_previous(self) -> None:
        """Test TenantContext restores previous tenant on exit."""
        set_current_tenant("original_tenant")

        with TenantContext("new_tenant"):
            assert get_current_tenant() == "new_tenant"

        assert get_current_tenant() == "original_tenant"
        set_current_tenant(None)

    @pytest.mark.asyncio
    async def test_tenant_context_async(self) -> None:
        """Test TenantContext as async context manager."""
        set_current_tenant(None)
        assert get_current_tenant() is None

        async with TenantContext("async_tenant"):
            assert get_current_tenant() == "async_tenant"

        assert get_current_tenant() is None


class TestTenantMiddleware:
    """Tests for TenantMiddleware class.

    **Feature: test-coverage-80-percent-v3**
    **Validates: Requirements 7.3**
    """

    @pytest.fixture()
    def mock_app(self) -> AsyncMock:
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_extracts_tenant_from_header(self, mock_app: AsyncMock) -> None:
        """Test middleware extracts tenant ID from header."""
        middleware = TenantMiddleware(mock_app, header_name="X-Tenant-ID")

        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"tenant_from_header")],
        }

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_through_non_http_requests(self, mock_app: AsyncMock) -> None:
        """Test middleware passes through non-HTTP requests."""
        middleware = TenantMiddleware(mock_app)

        scope = {"type": "websocket"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_sanitizes_invalid_tenant_id(self, mock_app: AsyncMock) -> None:
        """Test middleware rejects invalid tenant IDs."""
        middleware = TenantMiddleware(mock_app)

        # SQL injection attempt
        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"'; DROP TABLE users;--")],
        }

        await middleware(scope, AsyncMock(), AsyncMock())
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_empty_tenant_id(self, mock_app: AsyncMock) -> None:
        """Test middleware rejects empty tenant IDs."""
        middleware = TenantMiddleware(mock_app)

        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"   ")],
        }

        await middleware(scope, AsyncMock(), AsyncMock())
        mock_app.assert_called_once()


class TestRequireTenantDecorator:
    """Tests for require_tenant decorator.

    **Feature: test-coverage-80-percent-v3**
    **Validates: Requirements 7.3**
    """

    @pytest.mark.asyncio
    async def test_raises_when_no_tenant(self) -> None:
        """Test decorator raises ValueError when no tenant is set."""
        set_current_tenant(None)

        @require_tenant
        async def protected_function() -> str:
            return "success"

        with pytest.raises(ValueError, match="Tenant context required"):
            await protected_function()

    @pytest.mark.asyncio
    async def test_allows_when_tenant_set(self) -> None:
        """Test decorator allows execution when tenant is set."""
        set_current_tenant("valid_tenant")

        @require_tenant
        async def protected_function() -> str:
            return "success"

        result = await protected_function()
        assert result == "success"
        set_current_tenant(None)


class TestTenantIsolationProperties:
    """Property-based tests for tenant isolation.

    **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
    **Validates: Requirements 7.3**
    """

    @given(
        tenant_id=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-"),
    )
    @settings(max_examples=100, deadline=5000)
    def test_tenant_context_isolation(self, tenant_id: str) -> None:
        """Property: Tenant context is properly isolated.

        **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
        **Validates: Requirements 7.3**
        """
        # Ensure clean state
        set_current_tenant(None)
        assert get_current_tenant() is None

        with TenantContext(tenant_id):
            assert get_current_tenant() == tenant_id

        # Context should be restored
        assert get_current_tenant() is None

    @given(
        tenant1=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
        tenant2=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    )
    @settings(max_examples=50, deadline=5000)
    def test_nested_tenant_contexts(self, tenant1: str, tenant2: str) -> None:
        """Property: Nested tenant contexts restore correctly.

        **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
        **Validates: Requirements 7.3**
        """
        set_current_tenant(None)

        with TenantContext(tenant1):
            assert get_current_tenant() == tenant1

            with TenantContext(tenant2):
                assert get_current_tenant() == tenant2

            assert get_current_tenant() == tenant1

        assert get_current_tenant() is None
