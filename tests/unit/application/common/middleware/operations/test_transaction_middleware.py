"""Unit tests for transaction middleware.

Tests TransactionConfig, TransactionMiddleware, and transaction boundary configuration.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.common.middleware.operations.transaction import (
    DEFAULT_TRANSACTION_CONFIG,
    TransactionConfig,
    TransactionMiddleware,
)
from core.base.patterns.result import Err, Ok


class TestTransactionConfig:
    """Tests for TransactionConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TransactionConfig()

        assert config.enabled is True
        assert config.read_only is False
        assert config.isolation_level is None
        assert config.timeout_seconds is None
        assert config.auto_commit is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = TransactionConfig(
            enabled=True,
            read_only=True,
            isolation_level="SERIALIZABLE",
            timeout_seconds=30,
            auto_commit=False,
        )

        assert config.enabled is True
        assert config.read_only is True
        assert config.isolation_level == "SERIALIZABLE"
        assert config.timeout_seconds == 30
        assert config.auto_commit is False

    def test_disabled_transaction(self) -> None:
        """Test disabled transaction configuration."""
        config = TransactionConfig(enabled=False)

        assert config.enabled is False

    def test_frozen_dataclass(self) -> None:
        """Test that config is immutable."""
        config = TransactionConfig()

        with pytest.raises(AttributeError):
            config.enabled = False  # type: ignore


class TestDefaultTransactionConfig:
    """Tests for DEFAULT_TRANSACTION_CONFIG."""

    def test_default_config_values(self) -> None:
        """Test default config has expected values."""
        assert DEFAULT_TRANSACTION_CONFIG.enabled is True
        assert DEFAULT_TRANSACTION_CONFIG.read_only is False
        assert DEFAULT_TRANSACTION_CONFIG.auto_commit is True



class TestTransactionMiddleware:
    """Tests for TransactionMiddleware."""

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def uow_factory(self, mock_uow: MagicMock) -> MagicMock:
        """Create UoW factory."""
        return MagicMock(return_value=mock_uow)

    @pytest.fixture
    def middleware(self, uow_factory: MagicMock) -> TransactionMiddleware:
        """Create middleware instance."""
        return TransactionMiddleware(uow_factory)

    @pytest.mark.asyncio
    async def test_executes_handler_with_transaction(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test handler is executed within transaction."""
        command = MagicMock()
        del command.transaction_config  # Remove attribute
        del command.get_transaction_config
        handler = AsyncMock(return_value=Ok("success"))

        result = await middleware(command, handler)

        assert result.is_ok()
        handler.assert_called_once_with(command)
        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_commits_on_success(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test transaction is committed on success."""
        command = MagicMock()
        del command.transaction_config
        del command.get_transaction_config
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_commit_on_error(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test transaction is not committed on error result."""
        command = MagicMock()
        del command.transaction_config
        del command.get_transaction_config
        handler = AsyncMock(return_value=Err("error"))

        await middleware(command, handler)

        mock_uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_bypasses_transaction_when_disabled(
        self,
        uow_factory: MagicMock,
    ) -> None:
        """Test transaction is bypassed when disabled."""
        middleware = TransactionMiddleware(uow_factory)

        @dataclass
        class DisabledCommand:
            @property
            def transaction_config(self) -> TransactionConfig:
                return TransactionConfig(enabled=False)

        command = DisabledCommand()
        handler = AsyncMock(return_value=Ok("success"))

        result = await middleware(command, handler)

        assert result.is_ok()
        uow_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_uses_command_transaction_config(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test uses transaction config from command."""
        mock_uow.set_read_only = MagicMock()
        mock_uow.set_isolation_level = MagicMock()
        mock_uow.set_timeout = MagicMock()

        @dataclass
        class ConfiguredCommand:
            @property
            def transaction_config(self) -> TransactionConfig:
                return TransactionConfig(
                    enabled=True,
                    read_only=True,
                    isolation_level="SERIALIZABLE",
                    timeout_seconds=30,
                )

        command = ConfiguredCommand()
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        mock_uow.set_read_only.assert_called_once_with(True)
        mock_uow.set_isolation_level.assert_called_once_with("SERIALIZABLE")
        mock_uow.set_timeout.assert_called_once_with(30)

    @pytest.mark.asyncio
    async def test_uses_get_transaction_config_method(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test uses get_transaction_config method from command."""

        class MethodConfigCommand:
            def get_transaction_config(self) -> TransactionConfig:
                return TransactionConfig(enabled=True, read_only=True)

        mock_uow.set_read_only = MagicMock()
        command = MethodConfigCommand()
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        mock_uow.set_read_only.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_uses_default_config_when_not_provided(
        self,
        uow_factory: MagicMock,
        mock_uow: MagicMock,
    ) -> None:
        """Test uses default config when command has no config."""
        custom_default = TransactionConfig(
            enabled=True,
            read_only=True,
        )
        middleware = TransactionMiddleware(uow_factory, default_config=custom_default)
        mock_uow.set_read_only = MagicMock()

        command = MagicMock()
        del command.transaction_config
        del command.get_transaction_config
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        mock_uow.set_read_only.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_no_auto_commit_when_disabled(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test no auto-commit when disabled in config."""

        @dataclass
        class NoAutoCommitCommand:
            @property
            def transaction_config(self) -> TransactionConfig:
                return TransactionConfig(enabled=True, auto_commit=False)

        command = NoAutoCommitCommand()
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        mock_uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_injects_uow_into_command(
        self,
        middleware: TransactionMiddleware,
        mock_uow: MagicMock,
    ) -> None:
        """Test UoW is injected into command if it has uow attribute."""

        class CommandWithUow:
            uow: MagicMock | None = None

        command = CommandWithUow()
        handler = AsyncMock(return_value=Ok("success"))

        await middleware(command, handler)

        assert command.uow == mock_uow


class TestGetTransactionConfig:
    """Tests for _get_transaction_config method."""

    @pytest.fixture
    def middleware(self) -> TransactionMiddleware:
        """Create middleware instance."""
        return TransactionMiddleware(lambda: MagicMock())

    def test_returns_property_config(self, middleware: TransactionMiddleware) -> None:
        """Test returns config from property."""

        class CommandWithProperty:
            @property
            def transaction_config(self) -> TransactionConfig:
                return TransactionConfig(read_only=True)

        command = CommandWithProperty()
        config = middleware._get_transaction_config(command)

        assert config.read_only is True

    def test_returns_method_config(self, middleware: TransactionMiddleware) -> None:
        """Test returns config from method."""

        class CommandWithMethod:
            def get_transaction_config(self) -> TransactionConfig:
                return TransactionConfig(isolation_level="SERIALIZABLE")

        command = CommandWithMethod()
        config = middleware._get_transaction_config(command)

        assert config.isolation_level == "SERIALIZABLE"

    def test_returns_default_when_no_config(
        self, middleware: TransactionMiddleware
    ) -> None:
        """Test returns default config when command has no config."""
        command = MagicMock()
        del command.transaction_config
        del command.get_transaction_config

        config = middleware._get_transaction_config(command)

        assert config == DEFAULT_TRANSACTION_CONFIG
