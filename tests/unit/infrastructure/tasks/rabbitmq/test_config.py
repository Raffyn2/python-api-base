"""Tests for RabbitMQ configuration.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import timedelta

import pytest

from infrastructure.tasks.rabbitmq.config import RabbitMQConfig


class TestRabbitMQConfig:
    """Tests for RabbitMQConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RabbitMQConfig()
        assert config.host == "localhost"
        assert config.port == 5672
        assert config.username == "guest"
        assert config.password == "guest"
        assert config.virtual_host == "/"
        assert config.queue_name == "tasks"
        assert config.exchange == ""
        assert config.routing_key == "tasks"
        assert config.prefetch_count == 10
        assert config.connection_timeout == timedelta(seconds=30)

    def test_custom_host_and_port(self) -> None:
        """Test custom host and port configuration."""
        config = RabbitMQConfig(host="rabbitmq.example.com", port=5673)
        assert config.host == "rabbitmq.example.com"
        assert config.port == 5673

    def test_custom_credentials(self) -> None:
        """Test custom credentials configuration."""
        config = RabbitMQConfig(username="myuser", password="mypassword")
        assert config.username == "myuser"
        assert config.password == "mypassword"

    def test_custom_virtual_host(self) -> None:
        """Test custom virtual host configuration."""
        config = RabbitMQConfig(virtual_host="/production")
        assert config.virtual_host == "/production"

    def test_custom_queue_settings(self) -> None:
        """Test custom queue settings configuration."""
        config = RabbitMQConfig(
            queue_name="my-tasks",
            exchange="my-exchange",
            routing_key="my-routing-key",
        )
        assert config.queue_name == "my-tasks"
        assert config.exchange == "my-exchange"
        assert config.routing_key == "my-routing-key"

    def test_custom_prefetch_count(self) -> None:
        """Test custom prefetch count configuration."""
        config = RabbitMQConfig(prefetch_count=50)
        assert config.prefetch_count == 50

    def test_custom_connection_timeout(self) -> None:
        """Test custom connection timeout configuration."""
        config = RabbitMQConfig(connection_timeout=timedelta(seconds=60))
        assert config.connection_timeout == timedelta(seconds=60)

    def test_url_property_default(self) -> None:
        """Test URL property with default values."""
        config = RabbitMQConfig()
        assert config.url == "amqp://guest:guest@localhost:5672//"

    def test_url_property_custom(self) -> None:
        """Test URL property with custom values."""
        config = RabbitMQConfig(
            host="rabbitmq.example.com",
            port=5673,
            username="admin",
            password="secret",
            virtual_host="/myapp",
        )
        assert config.url == "amqp://admin:secret@rabbitmq.example.com:5673//myapp"

    def test_frozen_dataclass(self) -> None:
        """Test that RabbitMQConfig is immutable."""
        config = RabbitMQConfig()
        with pytest.raises(AttributeError):
            config.host = "new-host"

    def test_full_configuration(self) -> None:
        """Test full configuration with all options."""
        config = RabbitMQConfig(
            host="mq.prod.example.com",
            port=5672,
            username="prod-user",
            password="prod-pass",
            virtual_host="/production",
            queue_name="production-tasks",
            exchange="task-exchange",
            routing_key="task.process",
            prefetch_count=100,
            connection_timeout=timedelta(minutes=1),
        )
        assert config.host == "mq.prod.example.com"
        assert config.queue_name == "production-tasks"
        assert config.prefetch_count == 100
        assert config.connection_timeout == timedelta(minutes=1)
