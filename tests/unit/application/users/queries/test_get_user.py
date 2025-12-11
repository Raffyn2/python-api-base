"""Unit tests for user query handlers.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.users.queries.read.get_user import (
    CountUsersHandler,
    CountUsersQuery,
    GetUserByEmailHandler,
    GetUserByEmailQuery,
    GetUserByIdHandler,
    GetUserByIdQuery,
    ListUsersHandler,
    ListUsersQuery,
)


class TestGetUserByIdQuery:
    """Tests for GetUserByIdQuery."""

    def test_create_query(self) -> None:
        """Query should be created with user_id."""
        query = GetUserByIdQuery(user_id="user-123")
        assert query.user_id == "user-123"

    def test_cache_key(self) -> None:
        """Query should generate correct cache key."""
        query = GetUserByIdQuery(user_id="user-123")
        assert query.get_cache_key() == "user:user-123"


class TestGetUserByIdHandler:
    """Tests for GetUserByIdHandler."""

    @pytest.fixture()
    def mock_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def handler(self, mock_repository: AsyncMock) -> GetUserByIdHandler:
        return GetUserByIdHandler(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_handle_user_found(self, handler: GetUserByIdHandler, mock_repository: AsyncMock) -> None:
        """Handler should return user data when found."""
        mock_user = MagicMock()
        mock_user.model_dump.return_value = {"id": "user-123", "email": "test@example.com"}
        mock_repository.get_by_id.return_value = mock_user

        query = GetUserByIdQuery(user_id="user-123")
        result = await handler.handle(query)

        assert result.is_ok()
        assert result.unwrap()["id"] == "user-123"

    @pytest.mark.asyncio
    async def test_handle_user_not_found(self, handler: GetUserByIdHandler, mock_repository: AsyncMock) -> None:
        """Handler should return None when user not found."""
        mock_repository.get_by_id.return_value = None

        query = GetUserByIdQuery(user_id="nonexistent")
        result = await handler.handle(query)

        assert result.is_ok()
        assert result.unwrap() is None

    @pytest.mark.asyncio
    async def test_handle_exception(self, handler: GetUserByIdHandler, mock_repository: AsyncMock) -> None:
        """Handler should return Err on exception."""
        mock_repository.get_by_id.side_effect = Exception("DB error")

        query = GetUserByIdQuery(user_id="user-123")
        result = await handler.handle(query)

        assert result.is_err()


class TestGetUserByEmailQuery:
    """Tests for GetUserByEmailQuery."""

    def test_create_query(self) -> None:
        query = GetUserByEmailQuery(email="test@example.com")
        assert query.email == "test@example.com"

    def test_cache_key(self) -> None:
        query = GetUserByEmailQuery(email="test@example.com")
        assert query.get_cache_key() == "user:email:test@example.com"


class TestGetUserByEmailHandler:
    """Tests for GetUserByEmailHandler."""

    @pytest.fixture()
    def mock_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def handler(self, mock_repository: AsyncMock) -> GetUserByEmailHandler:
        return GetUserByEmailHandler(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_handle_user_found(self, handler: GetUserByEmailHandler, mock_repository: AsyncMock) -> None:
        """Handler should return user data when found."""
        mock_user = MagicMock()
        mock_user.model_dump.return_value = {"id": "user-123", "email": "test@example.com"}
        mock_repository.get_by_email.return_value = mock_user

        query = GetUserByEmailQuery(email="test@example.com")
        result = await handler.handle(query)

        assert result.is_ok()
        assert result.unwrap()["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_handle_user_not_found(self, handler: GetUserByEmailHandler, mock_repository: AsyncMock) -> None:
        """Handler should return None when user not found."""
        mock_repository.get_by_email.return_value = None

        query = GetUserByEmailQuery(email="nonexistent@example.com")
        result = await handler.handle(query)

        assert result.is_ok()
        assert result.unwrap() is None

    @pytest.mark.asyncio
    async def test_handle_exception(self, handler: GetUserByEmailHandler, mock_repository: AsyncMock) -> None:
        """Handler should return Err on exception."""
        mock_repository.get_by_email.side_effect = Exception("DB error")

        query = GetUserByEmailQuery(email="test@example.com")
        result = await handler.handle(query)

        assert result.is_err()


class TestListUsersQuery:
    """Tests for ListUsersQuery."""

    def test_default_values(self) -> None:
        query = ListUsersQuery()
        assert query.page == 1
        assert query.page_size == 20
        assert query.include_inactive is False

    def test_cache_key(self) -> None:
        query = ListUsersQuery(page=2, page_size=10, include_inactive=True)
        assert query.get_cache_key() == "users:list:2:10:True"


class TestListUsersHandler:
    """Tests for ListUsersHandler."""

    @pytest.fixture()
    def mock_read_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def handler(self, mock_read_repository: AsyncMock) -> ListUsersHandler:
        return ListUsersHandler(read_repository=mock_read_repository)

    @pytest.mark.asyncio
    async def test_handle_success(self, handler: ListUsersHandler, mock_read_repository: AsyncMock) -> None:
        """Handler should return list of users."""
        mock_read_repository.list_all.return_value = [
            {"id": "user-1"},
            {"id": "user-2"},
        ]

        query = ListUsersQuery(page=1, page_size=10)
        result = await handler.handle(query)

        assert result.is_ok()
        assert len(result.unwrap()) == 2
        mock_read_repository.list_all.assert_called_once_with(limit=10, offset=0, include_inactive=False)

    @pytest.mark.asyncio
    async def test_handle_pagination_offset(self, handler: ListUsersHandler, mock_read_repository: AsyncMock) -> None:
        """Handler should calculate correct offset."""
        mock_read_repository.list_all.return_value = []

        query = ListUsersQuery(page=3, page_size=20)
        await handler.handle(query)

        mock_read_repository.list_all.assert_called_once_with(limit=20, offset=40, include_inactive=False)

    @pytest.mark.asyncio
    async def test_handle_exception(self, handler: ListUsersHandler, mock_read_repository: AsyncMock) -> None:
        """Handler should return Err on exception."""
        mock_read_repository.list_all.side_effect = Exception("DB error")

        query = ListUsersQuery()
        result = await handler.handle(query)

        assert result.is_err()


class TestCountUsersQuery:
    """Tests for CountUsersQuery."""

    def test_default_values(self) -> None:
        query = CountUsersQuery()
        assert query.include_inactive is False

    def test_cache_key(self) -> None:
        query = CountUsersQuery(include_inactive=True)
        assert query.get_cache_key() == "users:count:True"


class TestCountUsersHandler:
    """Tests for CountUsersHandler."""

    @pytest.fixture()
    def mock_read_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def handler(self, mock_read_repository: AsyncMock) -> CountUsersHandler:
        return CountUsersHandler(read_repository=mock_read_repository)

    @pytest.mark.asyncio
    async def test_handle_success(self, handler: CountUsersHandler, mock_read_repository: AsyncMock) -> None:
        """Handler should return user count."""
        mock_read_repository.count_all.return_value = 42

        query = CountUsersQuery()
        result = await handler.handle(query)

        assert result.is_ok()
        assert result.unwrap() == 42

    @pytest.mark.asyncio
    async def test_handle_exception(self, handler: CountUsersHandler, mock_read_repository: AsyncMock) -> None:
        """Handler should return Err on exception."""
        mock_read_repository.count_all.side_effect = Exception("DB error")

        query = CountUsersQuery()
        result = await handler.handle(query)

        assert result.is_err()
