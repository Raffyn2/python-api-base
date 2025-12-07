"""Tests for core/base/cqrs/command.py - Base Command class."""

from dataclasses import dataclass
from datetime import datetime

import pytest

from src.core.base.cqrs.command import BaseCommand


@dataclass(frozen=True)
class CreateUserCommand(BaseCommand):
    """Test command for creating a user."""

    username: str = ""
    email: str = ""


@dataclass(frozen=True)
class DeleteItemCommand(BaseCommand):
    """Test command for deleting an item."""

    item_id: str = ""


class TestBaseCommandInit:
    """Tests for BaseCommand initialization."""

    def test_command_has_auto_generated_id(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        assert cmd.command_id is not None
        assert len(cmd.command_id) > 0

    def test_command_has_timestamp(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        assert cmd.timestamp is not None
        assert isinstance(cmd.timestamp, datetime)

    def test_command_id_is_unique(self):
        cmd1 = CreateUserCommand(username="test1", email="test1@example.com")
        cmd2 = CreateUserCommand(username="test2", email="test2@example.com")
        assert cmd1.command_id != cmd2.command_id

    def test_correlation_id_default_none(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        assert cmd.correlation_id is None

    def test_user_id_default_none(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        assert cmd.user_id is None

    def test_custom_correlation_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            correlation_id="corr-123",
        )
        assert cmd.correlation_id == "corr-123"

    def test_custom_user_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            user_id="user-456",
        )
        assert cmd.user_id == "user-456"

    def test_custom_command_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            command_id="custom-id",
        )
        assert cmd.command_id == "custom-id"


class TestBaseCommandImmutability:
    """Tests for BaseCommand immutability."""

    def test_command_is_frozen(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        with pytest.raises(AttributeError):
            cmd.username = "changed"

    def test_command_id_is_frozen(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        with pytest.raises(AttributeError):
            cmd.command_id = "new-id"


class TestBaseCommandType:
    """Tests for command_type property."""

    def test_command_type_returns_class_name(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        assert cmd.command_type == "CreateUserCommand"

    def test_different_command_types(self):
        create_cmd = CreateUserCommand(username="test", email="test@example.com")
        delete_cmd = DeleteItemCommand(item_id="item-123")
        assert create_cmd.command_type == "CreateUserCommand"
        assert delete_cmd.command_type == "DeleteItemCommand"


class TestBaseCommandToDict:
    """Tests for to_dict method."""

    def test_to_dict_returns_dict(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        result = cmd.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_username(self):
        cmd = CreateUserCommand(username="testuser", email="test@example.com")
        result = cmd.to_dict()
        assert result["username"] == "testuser"

    def test_to_dict_contains_email(self):
        cmd = CreateUserCommand(username="test", email="user@example.com")
        result = cmd.to_dict()
        assert result["email"] == "user@example.com"

    def test_to_dict_contains_command_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            command_id="cmd-123",
        )
        result = cmd.to_dict()
        assert result["command_id"] == "cmd-123"

    def test_to_dict_contains_timestamp(self):
        cmd = CreateUserCommand(username="test", email="test@example.com")
        result = cmd.to_dict()
        assert "timestamp" in result
        assert isinstance(result["timestamp"], datetime)

    def test_to_dict_contains_correlation_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            correlation_id="corr-456",
        )
        result = cmd.to_dict()
        assert result["correlation_id"] == "corr-456"

    def test_to_dict_contains_user_id(self):
        cmd = CreateUserCommand(
            username="test",
            email="test@example.com",
            user_id="user-789",
        )
        result = cmd.to_dict()
        assert result["user_id"] == "user-789"


class TestBaseCommandEquality:
    """Tests for command equality."""

    def test_same_command_id_equals(self):
        cmd1 = CreateUserCommand(
            username="test",
            email="test@example.com",
            command_id="same-id",
        )
        cmd2 = CreateUserCommand(
            username="test",
            email="test@example.com",
            command_id="same-id",
        )
        # Note: timestamps will differ, so they won't be equal
        assert cmd1.command_id == cmd2.command_id

    def test_different_command_ids_not_equal(self):
        cmd1 = CreateUserCommand(username="test", email="test@example.com")
        cmd2 = CreateUserCommand(username="test", email="test@example.com")
        assert cmd1.command_id != cmd2.command_id


class TestDeleteItemCommand:
    """Tests for DeleteItemCommand."""

    def test_delete_command_has_item_id(self):
        cmd = DeleteItemCommand(item_id="item-123")
        assert cmd.item_id == "item-123"

    def test_delete_command_type(self):
        cmd = DeleteItemCommand(item_id="item-123")
        assert cmd.command_type == "DeleteItemCommand"

    def test_delete_command_to_dict(self):
        cmd = DeleteItemCommand(item_id="item-456")
        result = cmd.to_dict()
        assert result["item_id"] == "item-456"
