"""Unit tests for CreateUserCommand and CreateUserHandler.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.users.commands.mutations.create_user import (
    CreateUserCommand,
    CreateUserHandler,
)
from core.base.patterns.result import Err, Ok


class TestCreateUserCommand:
    """Tests for CreateUserCommand dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Command should be created with required fields."""
        command = CreateUserCommand(
            email="test@example.com",
            password="SecurePass123!",
        )

        assert command.email == "test@example.com"
        assert command.password == "SecurePass123!"
        assert command.username is None
        assert command.display_name is None

    def test_create_with_all_fields(self) -> None:
        """Command should accept all optional fields."""
        command = CreateUserCommand(
            email="test@example.com",
            password="SecurePass123!",
            username="testuser",
            display_name="Test User",
        )

        assert command.email == "test@example.com"
        assert command.password == "SecurePass123!"
        assert command.username == "testuser"
        assert command.display_name == "Test User"

    def test_command_is_frozen(self) -> None:
        """Command should be immutable."""
        command = CreateUserCommand(
            email="test@example.com",
            password="SecurePass123!",
        )

        with pytest.raises(AttributeError):
            command.email = "other@example.com"  # type: ignore


class TestCreateUserHandler:
    """Tests for CreateUserHandler."""

    @pytest.fixture()
    def mock_repository(self) -> AsyncMock:
        """Create mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture()
    def mock_service(self) -> MagicMock:
        """Create mock user domain service."""
        service = MagicMock()
        service.hash_password.return_value = "hashed_password"
        return service

    @pytest.fixture()
    def mock_validator(self) -> AsyncMock:
        """Create mock validator."""
        validator = AsyncMock()
        validator.validate.return_value = Ok(None)
        return validator

    @pytest.fixture()
    def handler(
        self,
        mock_repository: AsyncMock,
        mock_service: MagicMock,
        mock_validator: AsyncMock,
    ) -> CreateUserHandler:
        """Create handler with mocked dependencies."""
        return CreateUserHandler(
            user_repository=mock_repository,
            user_service=mock_service,
            validator=mock_validator,
        )

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: CreateUserHandler,
        mock_repository: AsyncMock,
        mock_service: MagicMock,
        mock_validator: AsyncMock,
    ) -> None:
        """Handler should create user on valid command."""
        command = CreateUserCommand(
            email="test@example.com",
            password="SecurePass123!",
            username="testuser",
        )

        # Mock repository to return the saved user
        mock_repository.save.return_value = MagicMock(
            id="user-123",
            email="test@example.com",
        )

        result = await handler.handle(command)

        assert result.is_ok()
        mock_validator.validate.assert_called_once_with(command)
        mock_service.hash_password.assert_called_once_with("SecurePass123!")
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_validation_failure(
        self,
        handler: CreateUserHandler,
        mock_validator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should return error on validation failure."""
        command = CreateUserCommand(
            email="invalid-email",
            password="weak",
        )

        # Mock validation failure
        mock_validator.validate.return_value = Err(ValueError("Invalid email"))

        result = await handler.handle(command)

        assert result.is_err()
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_repository_exception(
        self,
        handler: CreateUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should propagate repository exceptions."""
        command = CreateUserCommand(
            email="test@example.com",
            password="SecurePass123!",
        )

        mock_repository.save.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await handler.handle(command)
