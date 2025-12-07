"""Unit tests for application constants.

Tests that constants have expected values and types.
"""

from core.config.application.constants import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
    CORS_MAX_AGE_SECONDS,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_REQUEST_SIZE_BYTES,
    DELETE_RATE_LIMIT_REQUESTS,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
    HTTP_UNPROCESSABLE_ENTITY,
    IMPORT_REQUEST_SIZE_BYTES,
    JWKS_CACHE_MAX_AGE_SECONDS,
    MAX_EMAIL_LENGTH,
    MAX_PAGE_SIZE,
    MAX_PASSWORD_LENGTH,
    MAX_STORAGE_LIST_KEYS,
    MIN_EMAIL_LENGTH,
    MIN_PAGE_NUMBER,
    MIN_PASSWORD_LENGTH,
    PRESIGNED_URL_EXPIRE_SECONDS,
    READ_RATE_LIMIT_REQUESTS,
    REFRESH_TOKEN_EXPIRE_SECONDS,
    STORAGE_TTL_DEFAULT_SECONDS,
    STORAGE_TTL_MAX_SECONDS,
    STORAGE_TTL_MIN_SECONDS,
    UPLOAD_REQUEST_SIZE_BYTES,
    WRITE_RATE_LIMIT_REQUESTS,
)


class TestRequestSizeLimits:
    """Tests for request size limit constants."""

    def test_default_request_size(self) -> None:
        """Test default request size is 10MB."""
        assert DEFAULT_REQUEST_SIZE_BYTES == 10 * 1024 * 1024

    def test_upload_request_size(self) -> None:
        """Test upload request size is 50MB."""
        assert UPLOAD_REQUEST_SIZE_BYTES == 50 * 1024 * 1024

    def test_import_request_size(self) -> None:
        """Test import request size is 20MB."""
        assert IMPORT_REQUEST_SIZE_BYTES == 20 * 1024 * 1024

    def test_size_ordering(self) -> None:
        """Test size limits are in expected order."""
        assert DEFAULT_REQUEST_SIZE_BYTES < IMPORT_REQUEST_SIZE_BYTES
        assert IMPORT_REQUEST_SIZE_BYTES < UPLOAD_REQUEST_SIZE_BYTES


class TestCacheTTL:
    """Tests for cache TTL constants."""

    def test_jwks_cache_max_age(self) -> None:
        """Test JWKS cache max age is 5 minutes."""
        assert JWKS_CACHE_MAX_AGE_SECONDS == 300

    def test_all_ttl_positive(self) -> None:
        """Test all TTL values are positive."""
        assert JWKS_CACHE_MAX_AGE_SECONDS > 0


class TestTokenExpiration:
    """Tests for token expiration constants."""

    def test_access_token_expire(self) -> None:
        """Test access token expires in 1 hour."""
        assert ACCESS_TOKEN_EXPIRE_SECONDS == 3600

    def test_refresh_token_expire(self) -> None:
        """Test refresh token expires in 7 days."""
        assert REFRESH_TOKEN_EXPIRE_SECONDS == 86400 * 7

    def test_refresh_longer_than_access(self) -> None:
        """Test refresh token lives longer than access token."""
        assert REFRESH_TOKEN_EXPIRE_SECONDS > ACCESS_TOKEN_EXPIRE_SECONDS


class TestRateLimiting:
    """Tests for rate limiting constants."""

    def test_default_rate_limit(self) -> None:
        """Test default rate limit."""
        assert DEFAULT_RATE_LIMIT_REQUESTS == 100

    def test_read_rate_limit(self) -> None:
        """Test read rate limit."""
        assert READ_RATE_LIMIT_REQUESTS == 100

    def test_write_rate_limit(self) -> None:
        """Test write rate limit is lower than read."""
        assert WRITE_RATE_LIMIT_REQUESTS == 20
        assert WRITE_RATE_LIMIT_REQUESTS < READ_RATE_LIMIT_REQUESTS

    def test_delete_rate_limit(self) -> None:
        """Test delete rate limit is lowest."""
        assert DELETE_RATE_LIMIT_REQUESTS == 10
        assert DELETE_RATE_LIMIT_REQUESTS < WRITE_RATE_LIMIT_REQUESTS


class TestPagination:
    """Tests for pagination constants."""

    def test_default_page_size(self) -> None:
        """Test default page size."""
        assert DEFAULT_PAGE_SIZE == 20

    def test_max_page_size(self) -> None:
        """Test max page size."""
        assert MAX_PAGE_SIZE == 100

    def test_min_page_number(self) -> None:
        """Test min page number."""
        assert MIN_PAGE_NUMBER == 1

    def test_page_size_ordering(self) -> None:
        """Test page size ordering."""
        assert DEFAULT_PAGE_SIZE <= MAX_PAGE_SIZE


class TestCORS:
    """Tests for CORS constants."""

    def test_cors_max_age(self) -> None:
        """Test CORS max age is 24 hours."""
        assert CORS_MAX_AGE_SECONDS == 86400


class TestStorageTTL:
    """Tests for storage TTL constants."""

    def test_storage_ttl_min(self) -> None:
        """Test minimum storage TTL."""
        assert STORAGE_TTL_MIN_SECONDS == 1

    def test_storage_ttl_max(self) -> None:
        """Test maximum storage TTL is 24 hours."""
        assert STORAGE_TTL_MAX_SECONDS == 86400

    def test_storage_ttl_default(self) -> None:
        """Test default storage TTL is 1 hour."""
        assert STORAGE_TTL_DEFAULT_SECONDS == 3600

    def test_presigned_url_expire(self) -> None:
        """Test presigned URL expiration."""
        assert PRESIGNED_URL_EXPIRE_SECONDS == 3600

    def test_max_storage_list_keys(self) -> None:
        """Test max storage list keys."""
        assert MAX_STORAGE_LIST_KEYS == 100


class TestFieldLimits:
    """Tests for field limit constants."""

    def test_email_length_range(self) -> None:
        """Test email length range."""
        assert MIN_EMAIL_LENGTH == 5
        assert MAX_EMAIL_LENGTH == 255
        assert MIN_EMAIL_LENGTH < MAX_EMAIL_LENGTH

    def test_password_length_range(self) -> None:
        """Test password length range."""
        assert MIN_PASSWORD_LENGTH == 8
        assert MAX_PASSWORD_LENGTH == 128
        assert MIN_PASSWORD_LENGTH < MAX_PASSWORD_LENGTH


class TestHTTPStatusCodes:
    """Tests for HTTP status code constants."""

    def test_http_ok(self) -> None:
        """Test HTTP OK status."""
        assert HTTP_OK == 200

    def test_http_bad_request(self) -> None:
        """Test HTTP Bad Request status."""
        assert HTTP_BAD_REQUEST == 400

    def test_http_unprocessable_entity(self) -> None:
        """Test HTTP Unprocessable Entity status."""
        assert HTTP_UNPROCESSABLE_ENTITY == 422

    def test_http_internal_server_error(self) -> None:
        """Test HTTP Internal Server Error status."""
        assert HTTP_INTERNAL_SERVER_ERROR == 500

    def test_http_service_unavailable(self) -> None:
        """Test HTTP Service Unavailable status."""
        assert HTTP_SERVICE_UNAVAILABLE == 503
