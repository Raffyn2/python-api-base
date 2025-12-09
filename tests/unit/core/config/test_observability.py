"""Unit tests for core/config/observability/observability.py.

Tests observability configuration and validation.

**Task 3.2: Create tests for observability configuration**
**Requirements: 3.2**
"""

import pytest
from pydantic import SecretStr

from core.config.observability.observability import ObservabilitySettings


class TestObservabilitySettings:
    """Tests for ObservabilitySettings class."""

    def test_default_values(self) -> None:
        """Test default observability settings."""
        settings = ObservabilitySettings()

        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.log_ecs_format is True
        assert settings.log_pii_redaction is True
        assert settings.service_name == "python-api-base"
        assert settings.environment == "development"
        assert settings.enable_tracing is True
        assert settings.enable_metrics is True

    def test_log_level_validation_valid(self) -> None:
        """Test valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = ObservabilitySettings(log_level=level)
            assert settings.log_level == level

    def test_log_level_validation_invalid(self) -> None:
        """Test invalid log level raises error."""
        with pytest.raises(ValueError):
            ObservabilitySettings(log_level="INVALID")

    def test_log_format_validation_valid(self) -> None:
        """Test valid log formats."""
        for fmt in ["json", "console"]:
            settings = ObservabilitySettings(log_format=fmt)
            assert settings.log_format == fmt

    def test_log_format_validation_invalid(self) -> None:
        """Test invalid log format raises error."""
        with pytest.raises(ValueError):
            ObservabilitySettings(log_format="xml")

    def test_otlp_endpoint_optional(self) -> None:
        """Test OTLP endpoint is optional."""
        settings = ObservabilitySettings()
        assert settings.otlp_endpoint is None

    def test_otlp_endpoint_custom(self) -> None:
        """Test custom OTLP endpoint."""
        settings = ObservabilitySettings(otlp_endpoint="http://collector:4317")
        assert settings.otlp_endpoint == "http://collector:4317"


class TestObservabilitySettingsElasticsearch:
    """Tests for Elasticsearch configuration."""

    def test_elasticsearch_defaults(self) -> None:
        """Test Elasticsearch default settings."""
        settings = ObservabilitySettings()

        assert settings.elasticsearch_enabled is False
        assert settings.elasticsearch_hosts == ["http://localhost:9200"]
        assert settings.elasticsearch_index_prefix == "logs-python-api-base"
        assert settings.elasticsearch_batch_size == 100
        assert settings.elasticsearch_flush_interval == 5.0

    def test_elasticsearch_batch_size_validation(self) -> None:
        """Test batch size validation."""
        with pytest.raises(ValueError):
            ObservabilitySettings(elasticsearch_batch_size=0)

        with pytest.raises(ValueError):
            ObservabilitySettings(elasticsearch_batch_size=1001)

    def test_elasticsearch_flush_interval_validation(self) -> None:
        """Test flush interval validation."""
        with pytest.raises(ValueError):
            ObservabilitySettings(elasticsearch_flush_interval=0.5)

        with pytest.raises(ValueError):
            ObservabilitySettings(elasticsearch_flush_interval=61.0)


class TestObservabilitySettingsKafka:
    """Tests for Kafka configuration."""

    def test_kafka_defaults(self) -> None:
        """Test Kafka default settings."""
        settings = ObservabilitySettings()

        assert settings.kafka_enabled is False
        assert settings.kafka_bootstrap_servers == ["localhost:9092"]
        assert settings.kafka_auto_offset_reset == "earliest"
        assert settings.kafka_enable_auto_commit is True

    def test_kafka_auto_offset_reset_validation(self) -> None:
        """Test auto_offset_reset validation."""
        settings = ObservabilitySettings(kafka_auto_offset_reset="latest")
        assert settings.kafka_auto_offset_reset == "latest"

        with pytest.raises(ValueError):
            ObservabilitySettings(kafka_auto_offset_reset="invalid")


class TestObservabilitySettingsCredentialValidation:
    """Tests for credential validation when services are enabled."""

    def test_minio_requires_credentials_when_enabled(self) -> None:
        """Test MinIO requires credentials when enabled."""
        with pytest.raises(ValueError, match="MinIO credentials required"):
            ObservabilitySettings(minio_enabled=True)

    def test_minio_with_credentials(self) -> None:
        """Test MinIO with valid credentials."""
        settings = ObservabilitySettings(
            minio_enabled=True,
            minio_access_key="access_key",
            minio_secret_key=SecretStr("secret_key"),
        )
        assert settings.minio_enabled is True

    def test_rabbitmq_requires_credentials_when_enabled(self) -> None:
        """Test RabbitMQ requires credentials when enabled."""
        with pytest.raises(ValueError, match="RabbitMQ credentials required"):
            ObservabilitySettings(rabbitmq_enabled=True)

    def test_rabbitmq_with_credentials(self) -> None:
        """Test RabbitMQ with valid credentials."""
        settings = ObservabilitySettings(
            rabbitmq_enabled=True,
            rabbitmq_username="user",
            rabbitmq_password=SecretStr("pass"),
        )
        assert settings.rabbitmq_enabled is True

    def test_keycloak_requires_secret_when_enabled(self) -> None:
        """Test Keycloak requires client secret when enabled."""
        with pytest.raises(ValueError, match="Keycloak client secret required"):
            ObservabilitySettings(keycloak_enabled=True)

    def test_keycloak_with_secret(self) -> None:
        """Test Keycloak with valid client secret."""
        settings = ObservabilitySettings(
            keycloak_enabled=True, keycloak_client_secret=SecretStr("secret")
        )
        assert settings.keycloak_enabled is True


class TestObservabilitySettingsPrometheus:
    """Tests for Prometheus configuration."""

    def test_prometheus_defaults(self) -> None:
        """Test Prometheus default settings."""
        settings = ObservabilitySettings()

        assert settings.prometheus_enabled is True
        assert settings.prometheus_endpoint == "/metrics"
        assert settings.prometheus_include_in_schema is False
        assert settings.prometheus_namespace == "python_api"


class TestObservabilitySettingsScyllaDB:
    """Tests for ScyllaDB configuration."""

    def test_scylladb_defaults(self) -> None:
        """Test ScyllaDB default settings."""
        settings = ObservabilitySettings()

        assert settings.scylladb_enabled is False
        assert settings.scylladb_hosts == ["localhost"]
        assert settings.scylladb_port == 9042
        assert settings.scylladb_keyspace == "python_api_base"
