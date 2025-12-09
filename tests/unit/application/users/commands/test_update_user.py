"""Unit tests for UpdateUserCommand and UpdateUserHandler.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.users.commands.mutations.update_user import (
    UpdateUserCommand,
    UpdateUserHandler,
)


class TestUpdateUserCommand:
    """Tests for UpdateUserCommand dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Command should be created with user_id."""
        command = UpdateUserCommand(user_id="user-123")

        assert command.user_id == "user-123"
        assert command.username is None
        assert command.display_name is None

    def test_create_with_all_fields(self) -> None:
        """Command should accept all optional fields."""
        command = UpdateUserCommand(
            user_id="user-123",
            username="newuser",
            display_name="New Name",
        )

        assert command.user_id == "user-123"
        assert command.username == "newuser"
        assert command.display_name == "New Name"

    def test_command_is_frozen(self) -> None:
        """Command should be immutable."""
        command = UpdateUserCommand(user_id="user-123")

        with pytest.raises(AttributeError):
            command.user_id = "other-id"  # type: ignore


class TestUpdateUserHandler:
    """Tests for UpdateUserHandler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def handler(self, mock_repository: AsyncMock) -> UpdateUserHandler:
        """Create handler with mocked dependencies."""
        return UpdateUserHandler(user_repository=mock_repository)

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: UpdateUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should update user successfully."""
        command = UpdateUserCommand(
            user_id="user-123",
            display_name="Updated Name",
        )

        # Mock repository to return existing user
        mock_user = MagicMock(id="user-123")
        mock_repository.get_by_id.return_value = mock_user
        mock_repository.save.return_value = mock_user

        result = await handler.handle(command)

        assert result.is_ok()
        mock_repository.get_by_id.assert_called_once_with("user-123")
        mock_user.update_profile.assert_called_once_with(
            username=None,
            display_name="Updated Name",
        )
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_not_found(
        self,
        handler: UpdateUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should return error when user not found."""
        command = UpdateUserCommand(user_id="nonexistent")

        mock_repository.get_by_id.return_value = None

        result = await handler.handle(command)

        assert result.is_err()
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_no_updates(
        self,
        handler: UpdateUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should not call update_profile when no fields provided."""
        command = UpdateUserCommand(user_id="user-123")

        mock_user = MagicMock(id="user-123")
        mock_repository.get_by_id.return_value = mock_user
        mock_repository.save.return_value = mock_user

        result = await handler.handle(command)

        assert result.is_ok()
        mock_user.update_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: UpdateUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should return Err on exception."""
        command = UpdateUserCommand(user_id="user-123")

        mock_repository.get_by_id.side_effect = Exception("DB error")

        result = await handler.handle(command)

        assert result.is_err()
