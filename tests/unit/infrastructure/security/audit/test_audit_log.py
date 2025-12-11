"""Unit tests for audit logging.

Tests AuditEntry, AuditFilters, and InMemoryAuditLogger.
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.security.audit.log import (
    AuditAction,
    AuditEntry,
    AuditFilters,
    AuditResult,
    InMemoryAuditLogger,
)


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_login_value(self) -> None:
        """Test LOGIN value."""
        assert AuditAction.LOGIN.value == "login"

    def test_logout_value(self) -> None:
        """Test LOGOUT value."""
        assert AuditAction.LOGOUT.value == "logout"

    def test_create_value(self) -> None:
        """Test CREATE value."""
        assert AuditAction.CREATE.value == "create"

    def test_read_value(self) -> None:
        """Test READ value."""
        assert AuditAction.READ.value == "read"

    def test_update_value(self) -> None:
        """Test UPDATE value."""
        assert AuditAction.UPDATE.value == "update"

    def test_delete_value(self) -> None:
        """Test DELETE value."""
        assert AuditAction.DELETE.value == "delete"


class TestAuditResult:
    """Tests for AuditResult enum."""

    def test_success_value(self) -> None:
        """Test SUCCESS value."""
        assert AuditResult.SUCCESS.value == "success"

    def test_failure_value(self) -> None:
        """Test FAILURE value."""
        assert AuditResult.FAILURE.value == "failure"

    def test_error_value(self) -> None:
        """Test ERROR value."""
        assert AuditResult.ERROR.value == "error"


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_creation(self) -> None:
        """Test AuditEntry creation."""
        entry = AuditEntry(
            id="test-id",
            timestamp=datetime.now(UTC),
            action="login",
            resource_type="user",
            result="success",
        )

        assert entry.id == "test-id"
        assert entry.action == "login"
        assert entry.resource_type == "user"
        assert entry.result == "success"

    def test_creation_with_all_fields(self) -> None:
        """Test AuditEntry creation with all fields."""
        entry = AuditEntry(
            id="test-id",
            timestamp=datetime.now(UTC),
            action="create",
            resource_type="document",
            result="success",
            user_id="user-123",
            resource_id="doc-456",
            details={"key": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
        )

        assert entry.user_id == "user-123"
        assert entry.resource_id == "doc-456"
        assert entry.details == {"key": "value"}
        assert entry.ip_address == "192.168.1.1"

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        timestamp = datetime.now(UTC)
        entry = AuditEntry(
            id="test-id",
            timestamp=timestamp,
            action="login",
            resource_type="user",
            result="success",
            user_id="user-123",
        )

        result = entry.to_dict()

        assert result["id"] == "test-id"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["action"] == "login"
        assert result["user_id"] == "user-123"

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "id": "test-id",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "action": "login",
            "resource_type": "user",
            "result": "success",
        }

        entry = AuditEntry.from_dict(data)

        assert entry.id == "test-id"
        assert entry.action == "login"

    def test_from_dict_with_datetime(self) -> None:
        """Test from_dict with datetime object."""
        timestamp = datetime.now(UTC)
        data = {
            "id": "test-id",
            "timestamp": timestamp,
            "action": "login",
            "resource_type": "user",
            "result": "success",
        }

        entry = AuditEntry.from_dict(data)

        assert entry.timestamp == timestamp

    def test_from_dict_naive_timestamp(self) -> None:
        """Test from_dict with naive timestamp."""
        data = {
            "id": "test-id",
            "timestamp": "2024-01-01T12:00:00",
            "action": "login",
            "resource_type": "user",
            "result": "success",
        }

        entry = AuditEntry.from_dict(data)

        assert entry.timestamp.tzinfo == UTC

    def test_from_dict_missing_required(self) -> None:
        """Test from_dict with missing required fields."""
        data = {"id": "test-id"}

        with pytest.raises(KeyError, match="Missing required fields"):
            AuditEntry.from_dict(data)

    def test_to_json(self) -> None:
        """Test to_json serialization."""
        entry = AuditEntry(
            id="test-id",
            timestamp=datetime.now(UTC),
            action="login",
            resource_type="user",
            result="success",
        )

        json_str = entry.to_json()

        assert "test-id" in json_str
        assert "login" in json_str

    def test_from_json(self) -> None:
        """Test from_json deserialization."""
        json_str = '{"id": "test-id", "timestamp": "2024-01-01T12:00:00+00:00", "action": "login", "resource_type": "user", "result": "success"}'

        entry = AuditEntry.from_json(json_str)

        assert entry.id == "test-id"
        assert entry.action == "login"


class TestAuditFilters:
    """Tests for AuditFilters dataclass."""

    def test_default_values(self) -> None:
        """Test default filter values."""
        filters = AuditFilters()

        assert filters.user_id is None
        assert filters.action is None
        assert filters.limit == 100
        assert filters.offset == 0

    def test_custom_values(self) -> None:
        """Test custom filter values."""
        filters = AuditFilters(
            user_id="user-123",
            action="login",
            resource_type="user",
            result="success",
            limit=50,
            offset=10,
        )

        assert filters.user_id == "user-123"
        assert filters.action == "login"
        assert filters.limit == 50
        assert filters.offset == 10


class TestInMemoryAuditLogger:
    """Tests for InMemoryAuditLogger."""

    @pytest.fixture()
    def logger(self) -> InMemoryAuditLogger:
        """Create logger instance."""
        return InMemoryAuditLogger(max_entries=100)

    @pytest.mark.asyncio
    async def test_log_entry(self, logger: InMemoryAuditLogger) -> None:
        """Test logging an entry."""
        entry = AuditEntry(
            id="test-id",
            timestamp=datetime.now(UTC),
            action="login",
            resource_type="user",
            result="success",
        )

        await logger.log(entry)

        results = await logger.query(AuditFilters())
        assert len(results) == 1
        assert results[0].id == "test-id"

    @pytest.mark.asyncio
    async def test_log_action(self, logger: InMemoryAuditLogger) -> None:
        """Test log_action convenience method."""
        entry = await logger.log_action(
            action=AuditAction.LOGIN,
            resource_type="user",
            result=AuditResult.SUCCESS,
            user_id="user-123",
        )

        assert entry.action == "login"
        assert entry.result == "success"
        assert entry.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_log_action_with_strings(self, logger: InMemoryAuditLogger) -> None:
        """Test log_action with string values."""
        entry = await logger.log_action(
            action="custom_action",
            resource_type="custom_resource",
            result="custom_result",
        )

        assert entry.action == "custom_action"
        assert entry.result == "custom_result"

    @pytest.mark.asyncio
    async def test_query_by_user_id(self, logger: InMemoryAuditLogger) -> None:
        """Test query filtering by user_id."""
        await logger.log_action(action="login", resource_type="user", user_id="user-1")
        await logger.log_action(action="login", resource_type="user", user_id="user-2")

        results = await logger.query(AuditFilters(user_id="user-1"))

        assert len(results) == 1
        assert results[0].user_id == "user-1"

    @pytest.mark.asyncio
    async def test_query_by_action(self, logger: InMemoryAuditLogger) -> None:
        """Test query filtering by action."""
        await logger.log_action(action="login", resource_type="user")
        await logger.log_action(action="logout", resource_type="user")

        results = await logger.query(AuditFilters(action="login"))

        assert len(results) == 1
        assert results[0].action == "login"

    @pytest.mark.asyncio
    async def test_query_by_resource_type(self, logger: InMemoryAuditLogger) -> None:
        """Test query filtering by resource_type."""
        await logger.log_action(action="create", resource_type="document")
        await logger.log_action(action="create", resource_type="user")

        results = await logger.query(AuditFilters(resource_type="document"))

        assert len(results) == 1
        assert results[0].resource_type == "document"

    @pytest.mark.asyncio
    async def test_query_by_result(self, logger: InMemoryAuditLogger) -> None:
        """Test query filtering by result."""
        await logger.log_action(action="login", resource_type="user", result=AuditResult.SUCCESS)
        await logger.log_action(action="login", resource_type="user", result=AuditResult.FAILURE)

        results = await logger.query(AuditFilters(result="success"))

        assert len(results) == 1
        assert results[0].result == "success"

    @pytest.mark.asyncio
    async def test_query_by_date_range(self, logger: InMemoryAuditLogger) -> None:
        """Test query filtering by date range."""
        now = datetime.now(UTC)
        old_entry = AuditEntry(
            id="old",
            timestamp=now - timedelta(days=2),
            action="login",
            resource_type="user",
            result="success",
        )
        new_entry = AuditEntry(
            id="new",
            timestamp=now,
            action="login",
            resource_type="user",
            result="success",
        )

        await logger.log(old_entry)
        await logger.log(new_entry)

        results = await logger.query(AuditFilters(start_date=now - timedelta(days=1)))

        assert len(results) == 1
        assert results[0].id == "new"

    @pytest.mark.asyncio
    async def test_query_pagination(self, logger: InMemoryAuditLogger) -> None:
        """Test query pagination."""
        for i in range(10):
            await logger.log_action(action="login", resource_type="user", user_id=f"user-{i}")

        results = await logger.query(AuditFilters(limit=5, offset=0))
        assert len(results) == 5

        results = await logger.query(AuditFilters(limit=5, offset=5))
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_max_entries_limit(self) -> None:
        """Test max entries limit trims old entries."""
        logger = InMemoryAuditLogger(max_entries=5)

        for i in range(10):
            await logger.log_action(action="login", resource_type="user", user_id=f"user-{i}")

        results = await logger.query(AuditFilters(limit=100))
        assert len(results) == 5

    def test_clear(self, logger: InMemoryAuditLogger) -> None:
        """Test clear removes all entries."""
        logger._entries.append(
            AuditEntry(
                id="test",
                timestamp=datetime.now(UTC),
                action="login",
                resource_type="user",
                result="success",
            )
        )

        logger.clear()

        assert len(logger._entries) == 0
