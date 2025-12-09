"""Unit tests for DeleteUserCommand and DeleteUserHandler.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.users.commands.mutations.delete_user import (
    DeleteUserCommand,
    DeleteUserHandler,
)


class TestDeleteUserCommand:
    """Tests for DeleteUserCommand dataclass."""

    def test_create_command(self) -> None:
        """Command should be created with user_id."""
        command = DeleteUserCommand(user_id="user-123")

        assert command.user_id == "user-123"
        assert command.reason == "User requested deletion"

    def test_create_with_custom_reason(self) -> None:
        """Command should accept custom reason."""
        command = DeleteUserCommand(
            user_id="user-123",
            reason="Admin action",
        )

        assert command.user_id == "user-123"
        assert command.reason == "Admin action"

    def test_command_is_frozen(self) -> None:
        """Command should be immutable."""
        command = DeleteUserCommand(user_id="user-123")

        with pytest.raises(AttributeError):
            command.user_id = "other-id"  # type: ignore


class TestDeleteUserHandler:
    """Tests for DeleteUserHandler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock user repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def handler(self, mock_repository: AsyncMock) -> DeleteUserHandler:
        """Create handler with mocked dependencies."""
        return DeleteUserHandler(user_repository=mock_repository)

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: DeleteUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should deactivate user successfully."""
        command = DeleteUserCommand(user_id="user-123")

        # Mock repository to return existing user
        mock_user = MagicMock(id="user-123")
        mock_repository.get_by_id.return_value = mock_user
        mock_repository.save.return_value = mock_user

        result = await handler.handle(command)

        assert result.is_ok()
        assert result.unwrap() is True
        mock_repository.get_by_id.assert_called_once_with("user-123")
        mock_user.deactivate.assert_called_once_with(reason="User requested deletion")
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_user_not_found(
        self,
        handler: DeleteUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should return error when user not found."""
        command = DeleteUserCommand(user_id="nonexistent")

        mock_repository.get_by_id.return_value = None

        result = await handler.handle(command)

        assert result.is_err()
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_custom_reason(
        self,
        handler: DeleteUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should pass custom reason to deactivate."""
        command = DeleteUserCommand(
            user_id="user-123",
            reason="Violation of terms",
        )

        mock_user = MagicMock(id="user-123")
        mock_repository.get_by_id.return_value = mock_user
        mock_repository.save.return_value = mock_user

        result = await handler.handle(command)

        assert result.is_ok()
        mock_user.deactivate.assert_called_once_with(reason="Violation of terms")

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: DeleteUserHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Handler should return Err on exception."""
        command = DeleteUserCommand(user_id="user-123")

        mock_repository.get_by_id.side_effect = Exception("DB error")

        result = await handler.handle(command)

        assert result.is_err()
