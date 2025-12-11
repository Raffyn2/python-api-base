"""Configuration validation and sanitization utilities.

**Feature: config-security-enhancement**

Provides centralized validation and sanitization of configuration values
to ensure security and prevent accidental exposure of sensitive data.
"""

from __future__ import annotations

from typing import Any, TypeVar

import structlog
from pydantic import BaseModel, ValidationError

from core.config.shared.utils import redact_url_credentials

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ConfigValidator:
    """Validates and sanitizes configuration values.

    Ensures that:
    1. All configuration is properly typed and validated (via Pydantic)
    2. Sensitive values are redacted before logging
    3. Missing required config triggers clear errors
    4. Invalid values are caught early (fail-fast)
    """

    @staticmethod
    def validate_and_redact(settings: T) -> T:
        """Validate settings and redact sensitive values for logging.

        Args:
            settings: Pydantic settings model to validate.

        Returns:
            Validated settings with sensitive values redacted.

        Raises:
            ValidationError: If settings validation fails.

        Example:
            >>> from core.config.application.settings import Settings
            >>> settings = Settings()
            >>> safe_settings = ConfigValidator.validate_and_redact(settings)
            >>> logger.info("config_loaded", settings=safe_settings)
        """
        try:
            # Pydantic already validates on initialization
            validated = settings

            # Redact sensitive values for safe logging
            ConfigValidator._redact_sensitive_fields(validated)

            return validated
        except ValidationError as e:
            logger.error("config_validation_failed", errors=e.errors())
            raise

    @staticmethod
    def _redact_sensitive_fields(settings: BaseModel) -> None:
        """Redact sensitive fields in-place for logging.

        Args:
            settings: Settings object to redact.
        """
        ConfigValidator._redact_database_url(settings)
        ConfigValidator._redact_redis_url(settings)
        ConfigValidator._redact_kafka_urls(settings)
        ConfigValidator._redact_elasticsearch_urls(settings)
        ConfigValidator._redact_minio_endpoint(settings)

    @staticmethod
    def _redact_database_url(settings: BaseModel) -> None:
        """Redact database URL if present."""
        if hasattr(settings, "database") and hasattr(settings.database, "url"):
            if settings.database.url:
                settings.database.url = redact_url_credentials(settings.database.url)

    @staticmethod
    def _redact_redis_url(settings: BaseModel) -> None:
        """Redact Redis URL if present."""
        if hasattr(settings, "redis") and hasattr(settings.redis, "url"):
            if settings.redis.url:
                settings.redis.url = redact_url_credentials(settings.redis.url)

    @staticmethod
    def _redact_kafka_urls(settings: BaseModel) -> None:
        """Redact Kafka bootstrap server URLs if present."""
        if hasattr(settings, "kafka") and hasattr(settings.kafka, "bootstrap_servers"):
            if settings.kafka.bootstrap_servers:
                redacted = [
                    redact_url_credentials(server) if "://" in server else server
                    for server in settings.kafka.bootstrap_servers
                ]
                settings.kafka.bootstrap_servers = redacted

    @staticmethod
    def _redact_elasticsearch_urls(settings: BaseModel) -> None:
        """Redact Elasticsearch host URLs if present."""
        if hasattr(settings, "elasticsearch") and hasattr(settings.elasticsearch, "hosts"):
            if settings.elasticsearch.hosts:
                redacted_hosts = [
                    redact_url_credentials(host) if isinstance(host, str) else host
                    for host in settings.elasticsearch.hosts
                ]
                settings.elasticsearch.hosts = redacted_hosts

    @staticmethod
    def _redact_minio_endpoint(settings: BaseModel) -> None:
        """Redact MinIO endpoint if present."""
        if hasattr(settings, "minio") and hasattr(settings.minio, "endpoint"):
            if settings.minio.endpoint and "://" in settings.minio.endpoint:
                settings.minio.endpoint = redact_url_credentials(settings.minio.endpoint)

    @staticmethod
    def validate_required_fields(settings: BaseModel, required_fields: list[str]) -> None:
        """Validate that required fields are present and not None/empty.

        Args:
            settings: Settings object to validate.
            required_fields: List of field paths to check (e.g., "database.url").

        Raises:
            ValueError: If any required field is missing or empty.

        Example:
            >>> ConfigValidator.validate_required_fields(
            ...     settings,
            ...     ["database.url", "redis.url", "security.secret_key"]
            ... )
        """
        missing_fields = []

        for field_path in required_fields:
            parts = field_path.split(".")
            value = settings

            # Navigate nested fields
            for part in parts:
                if not hasattr(value, part):
                    missing_fields.append(field_path)
                    break
                value = getattr(value, part)

            # Check if value is None or empty string
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field_path)

        if missing_fields:
            msg = f"Missing or empty required configuration fields: {', '.join(missing_fields)}"
            logger.error("config_required_fields_missing", fields=missing_fields)
            raise ValueError(msg)

    @staticmethod
    def get_safe_config_for_logging(settings: BaseModel) -> dict[str, Any]:
        """Get sanitized configuration dict safe for logging.

        Args:
            settings: Settings object to sanitize.

        Returns:
            Dictionary with sensitive values redacted.

        Example:
            >>> safe_config = ConfigValidator.get_safe_config_for_logging(settings)
            >>> logger.info("application_started", config=safe_config)
        """
        # Create a copy to avoid modifying original
        import copy

        settings_copy = copy.deepcopy(settings)
        ConfigValidator._redact_sensitive_fields(settings_copy)

        # Convert to dict for logging
        if hasattr(settings_copy, "model_dump"):
            # Pydantic v2
            return settings_copy.model_dump(mode="json")
        elif hasattr(settings_copy, "dict"):
            # Pydantic v1
            return settings_copy.dict()  # type: ignore[attr-defined]
        else:
            return {}


class ConfigValidationError(Exception):
    """Configuration validation error."""

    def __init__(self, message: str, *, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []
