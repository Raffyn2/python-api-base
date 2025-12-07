"""Tests for MinIO configuration.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import timedelta

import pytest

from infrastructure.minio.config import MinIOConfig


class TestMinIOConfig:
    """Tests for MinIOConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MinIOConfig()
        assert config.endpoint == "localhost:9000"
        assert config.access_key == "minioadmin"
        assert config.secret_key == "minioadmin"
        assert config.bucket == "uploads"
        assert config.secure is False
        assert config.region is None
        assert config.presigned_expiry == timedelta(hours=1)
        assert config.max_presigned_expiry == timedelta(hours=24)
        assert config.multipart_threshold == 5 * 1024 * 1024
        assert config.multipart_chunk_size == 5 * 1024 * 1024
        assert config.allowed_content_types is None
        assert config.max_file_size == 100 * 1024 * 1024

    def test_custom_endpoint(self) -> None:
        """Test custom endpoint configuration."""
        config = MinIOConfig(endpoint="minio.example.com:9000")
        assert config.endpoint == "minio.example.com:9000"

    def test_custom_credentials(self) -> None:
        """Test custom credentials configuration."""
        config = MinIOConfig(
            access_key="my-access-key",
            secret_key="my-secret-key",
        )
        assert config.access_key == "my-access-key"
        assert config.secret_key == "my-secret-key"

    def test_custom_bucket(self) -> None:
        """Test custom bucket configuration."""
        config = MinIOConfig(bucket="my-bucket")
        assert config.bucket == "my-bucket"

    def test_secure_mode(self) -> None:
        """Test secure mode configuration."""
        config = MinIOConfig(secure=True)
        assert config.secure is True

    def test_region_configuration(self) -> None:
        """Test region configuration."""
        config = MinIOConfig(region="us-east-1")
        assert config.region == "us-east-1"

    def test_presigned_expiry_configuration(self) -> None:
        """Test presigned URL expiry configuration."""
        config = MinIOConfig(
            presigned_expiry=timedelta(minutes=30),
            max_presigned_expiry=timedelta(hours=12),
        )
        assert config.presigned_expiry == timedelta(minutes=30)
        assert config.max_presigned_expiry == timedelta(hours=12)

    def test_multipart_configuration(self) -> None:
        """Test multipart upload configuration."""
        config = MinIOConfig(
            multipart_threshold=10 * 1024 * 1024,
            multipart_chunk_size=8 * 1024 * 1024,
        )
        assert config.multipart_threshold == 10 * 1024 * 1024
        assert config.multipart_chunk_size == 8 * 1024 * 1024

    def test_allowed_content_types(self) -> None:
        """Test allowed content types configuration."""
        config = MinIOConfig(
            allowed_content_types=["image/jpeg", "image/png", "application/pdf"]
        )
        assert config.allowed_content_types == [
            "image/jpeg",
            "image/png",
            "application/pdf",
        ]

    def test_max_file_size(self) -> None:
        """Test max file size configuration."""
        config = MinIOConfig(max_file_size=50 * 1024 * 1024)
        assert config.max_file_size == 50 * 1024 * 1024

    def test_full_configuration(self) -> None:
        """Test full configuration with all options."""
        config = MinIOConfig(
            endpoint="s3.amazonaws.com",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            bucket="production-bucket",
            secure=True,
            region="us-west-2",
            presigned_expiry=timedelta(hours=2),
            max_presigned_expiry=timedelta(hours=48),
            multipart_threshold=20 * 1024 * 1024,
            multipart_chunk_size=10 * 1024 * 1024,
            allowed_content_types=["image/*"],
            max_file_size=500 * 1024 * 1024,
        )
        assert config.endpoint == "s3.amazonaws.com"
        assert config.secure is True
        assert config.region == "us-west-2"
        assert config.max_file_size == 500 * 1024 * 1024
