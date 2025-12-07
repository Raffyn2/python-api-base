"""Tests for core/base/events/integration_event.py - Integration events."""

from datetime import datetime

import pytest

from src.core.base.events.integration_event import (
    IntegrationEvent,
    OrderCreatedIntegrationEvent,
    UserDeactivatedIntegrationEvent,
    UserRegisteredIntegrationEvent,
)


class TestIntegrationEvent:
    """Tests for IntegrationEvent base class."""

    def test_auto_generates_event_id(self):
        event = IntegrationEvent()
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_event_id_is_unique(self):
        event1 = IntegrationEvent()
        event2 = IntegrationEvent()
        assert event1.event_id != event2.event_id

    def test_occurred_at_is_set(self):
        event = IntegrationEvent()
        assert event.occurred_at is not None
        assert isinstance(event.occurred_at, datetime)

    def test_source_context_default_empty(self):
        event = IntegrationEvent()
        assert event.source_context == ""

    def test_correlation_id_default_none(self):
        event = IntegrationEvent()
        assert event.correlation_id is None

    def test_causation_id_default_none(self):
        event = IntegrationEvent()
        assert event.causation_id is None

    def test_version_default_one(self):
        event = IntegrationEvent()
        assert event.version == 1

    def test_custom_source_context(self):
        event = IntegrationEvent(source_context="orders")
        assert event.source_context == "orders"

    def test_custom_correlation_id(self):
        event = IntegrationEvent(correlation_id="corr-123")
        assert event.correlation_id == "corr-123"

    def test_custom_causation_id(self):
        event = IntegrationEvent(causation_id="cause-456")
        assert event.causation_id == "cause-456"

    def test_custom_version(self):
        event = IntegrationEvent(version=2)
        assert event.version == 2


class TestIntegrationEventType:
    """Tests for event_type property."""

    def test_event_type_includes_source_context(self):
        event = IntegrationEvent(source_context="users")
        assert "users" in event.event_type

    def test_event_type_includes_class_name(self):
        event = IntegrationEvent(source_context="users")
        assert "IntegrationEvent" in event.event_type

    def test_event_type_format(self):
        event = IntegrationEvent(source_context="orders")
        assert event.event_type == "orders.IntegrationEvent"


class TestIntegrationEventToDict:
    """Tests for to_dict method."""

    def test_to_dict_returns_dict(self):
        event = IntegrationEvent()
        result = event.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_event_id(self):
        event = IntegrationEvent(event_id="evt-123")
        result = event.to_dict()
        assert result["event_id"] == "evt-123"

    def test_to_dict_contains_event_type(self):
        event = IntegrationEvent(source_context="test")
        result = event.to_dict()
        assert result["event_type"] == "test.IntegrationEvent"

    def test_to_dict_contains_occurred_at_iso(self):
        event = IntegrationEvent()
        result = event.to_dict()
        assert "occurred_at" in result
        assert isinstance(result["occurred_at"], str)

    def test_to_dict_contains_source_context(self):
        event = IntegrationEvent(source_context="users")
        result = event.to_dict()
        assert result["source_context"] == "users"

    def test_to_dict_contains_correlation_id(self):
        event = IntegrationEvent(correlation_id="corr-789")
        result = event.to_dict()
        assert result["correlation_id"] == "corr-789"

    def test_to_dict_contains_causation_id(self):
        event = IntegrationEvent(causation_id="cause-abc")
        result = event.to_dict()
        assert result["causation_id"] == "cause-abc"

    def test_to_dict_contains_version(self):
        event = IntegrationEvent(version=3)
        result = event.to_dict()
        assert result["version"] == 3

    def test_to_dict_contains_payload(self):
        event = IntegrationEvent()
        result = event.to_dict()
        assert "payload" in result
        assert result["payload"] == {}


class TestIntegrationEventImmutability:
    """Tests for event immutability."""

    def test_event_is_frozen(self):
        event = IntegrationEvent()
        with pytest.raises(AttributeError):
            event.event_id = "new-id"


class TestUserRegisteredIntegrationEvent:
    """Tests for UserRegisteredIntegrationEvent."""

    def test_user_id_field(self):
        event = UserRegisteredIntegrationEvent(user_id="user-123")
        assert event.user_id == "user-123"

    def test_email_field(self):
        event = UserRegisteredIntegrationEvent(email="test@example.com")
        assert event.email == "test@example.com"

    def test_source_context_is_users(self):
        event = UserRegisteredIntegrationEvent()
        assert event.source_context == "users"

    def test_event_type(self):
        event = UserRegisteredIntegrationEvent()
        assert event.event_type == "users.UserRegisteredIntegrationEvent"

    def test_payload_contains_user_id(self):
        event = UserRegisteredIntegrationEvent(user_id="user-456")
        result = event.to_dict()
        assert result["payload"]["user_id"] == "user-456"

    def test_payload_contains_email(self):
        event = UserRegisteredIntegrationEvent(email="user@test.com")
        result = event.to_dict()
        assert result["payload"]["email"] == "user@test.com"


class TestUserDeactivatedIntegrationEvent:
    """Tests for UserDeactivatedIntegrationEvent."""

    def test_user_id_field(self):
        event = UserDeactivatedIntegrationEvent(user_id="user-789")
        assert event.user_id == "user-789"

    def test_reason_field(self):
        event = UserDeactivatedIntegrationEvent(reason="Account closed")
        assert event.reason == "Account closed"

    def test_source_context_is_users(self):
        event = UserDeactivatedIntegrationEvent()
        assert event.source_context == "users"

    def test_event_type(self):
        event = UserDeactivatedIntegrationEvent()
        assert event.event_type == "users.UserDeactivatedIntegrationEvent"

    def test_payload_contains_user_id(self):
        event = UserDeactivatedIntegrationEvent(user_id="user-abc")
        result = event.to_dict()
        assert result["payload"]["user_id"] == "user-abc"

    def test_payload_contains_reason(self):
        event = UserDeactivatedIntegrationEvent(reason="Inactive")
        result = event.to_dict()
        assert result["payload"]["reason"] == "Inactive"


class TestOrderCreatedIntegrationEvent:
    """Tests for OrderCreatedIntegrationEvent."""

    def test_order_id_field(self):
        event = OrderCreatedIntegrationEvent(order_id="order-123")
        assert event.order_id == "order-123"

    def test_user_id_field(self):
        event = OrderCreatedIntegrationEvent(user_id="user-456")
        assert event.user_id == "user-456"

    def test_total_amount_field(self):
        event = OrderCreatedIntegrationEvent(total_amount=99.99)
        assert event.total_amount == 99.99

    def test_source_context_is_orders(self):
        event = OrderCreatedIntegrationEvent()
        assert event.source_context == "orders"

    def test_event_type(self):
        event = OrderCreatedIntegrationEvent()
        assert event.event_type == "orders.OrderCreatedIntegrationEvent"

    def test_payload_contains_order_id(self):
        event = OrderCreatedIntegrationEvent(order_id="ord-xyz")
        result = event.to_dict()
        assert result["payload"]["order_id"] == "ord-xyz"

    def test_payload_contains_user_id(self):
        event = OrderCreatedIntegrationEvent(user_id="usr-abc")
        result = event.to_dict()
        assert result["payload"]["user_id"] == "usr-abc"

    def test_payload_contains_total_amount(self):
        event = OrderCreatedIntegrationEvent(total_amount=150.50)
        result = event.to_dict()
        assert result["payload"]["total_amount"] == 150.50
