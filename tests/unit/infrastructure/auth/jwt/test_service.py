"""Unit tests for JWT service.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 4.2, Property 9: JWT Round-trip**
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from infrastructure.auth.jwt.errors import (
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)
from infrastructure.auth.jwt.service import JWTService
from infrastructure.auth.jwt.time_source import TimeSource


class MockTimeSource(TimeSource):
    """Mock time source for testing."""

    def __init__(self, fixed_time: datetime | None = None) -> None:
        self._time = fixed_time or datetime.now(UTC)

    def now(self) -> datetime:
        return self._time

    def advance(self, delta: timedelta) -> None:
        """Advance time by delta."""
        self._time = self._time + delta


class TestJWTService:
    """Tests for JWTService class."""

    @pytest.fixture
    def secret_key(self) -> str:
        """Create test secret key (32+ chars)."""
        return "test-secret-key-that-is-at-least-32-characters-long"

    @pytest.fixture
    def time_source(self) -> MockTimeSource:
        """Create mock time source."""
        return MockTimeSource()

    @pytest.fixture
    def service(self, secret_key: str, time_source: MockTimeSource) -> JWTService:
        """Create JWT service with mock time source."""
        return JWTService(
            secret_key=secret_key,
            time_source=time_source,
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )


    def test_init_rejects_short_secret(self) -> None:
        """Test service rejects secret key shorter than 32 chars."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            JWTService(secret_key="short")

    def test_create_access_token(self, service: JWTService) -> None:
        """Test creating access token."""
        token, payload = service.create_access_token("user123")

        assert token is not None
        assert payload.sub == "user123"
        assert payload.token_type == "access"
        assert payload.jti is not None

    def test_create_access_token_with_scopes(self, service: JWTService) -> None:
        """Test creating access token with scopes."""
        token, payload = service.create_access_token(
            "user123", scopes=["read", "write"]
        )

        assert payload.scopes == ("read", "write")

    def test_create_refresh_token(self, service: JWTService) -> None:
        """Test creating refresh token."""
        token, payload = service.create_refresh_token("user123")

        assert token is not None
        assert payload.sub == "user123"
        assert payload.token_type == "refresh"

    def test_create_token_pair(self, service: JWTService) -> None:
        """Test creating token pair."""
        pair, access_payload, refresh_payload = service.create_token_pair("user123")

        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert access_payload.token_type == "access"
        assert refresh_payload.token_type == "refresh"

    def test_verify_valid_token(self, service: JWTService) -> None:
        """Test verifying valid token."""
        token, _ = service.create_access_token("user123")

        payload = service.verify_token(token)

        assert payload.sub == "user123"

    def test_verify_token_with_expected_type(self, service: JWTService) -> None:
        """Test verifying token with expected type."""
        token, _ = service.create_access_token("user123")

        payload = service.verify_token(token, expected_type="access")

        assert payload.token_type == "access"


    def test_verify_token_wrong_type_fails(self, service: JWTService) -> None:
        """Test verifying token with wrong type fails."""
        token, _ = service.create_access_token("user123")

        with pytest.raises(TokenInvalidError, match="Expected refresh"):
            service.verify_token(token, expected_type="refresh")

    def test_verify_expired_token_fails(
        self, service: JWTService, time_source: MockTimeSource
    ) -> None:
        """Test verifying expired token fails."""
        token, _ = service.create_access_token("user123")

        # Advance time past expiration
        time_source.advance(timedelta(hours=2))

        with pytest.raises(TokenExpiredError):
            service.verify_token(token)

    def test_verify_invalid_token_fails(self, service: JWTService) -> None:
        """Test verifying invalid token fails."""
        with pytest.raises(TokenInvalidError):
            service.verify_token("invalid.token.here")

    def test_verify_refresh_token(self, service: JWTService) -> None:
        """Test verifying refresh token."""
        token, _ = service.create_refresh_token("user123")

        payload = service.verify_refresh_token(token)

        assert payload.sub == "user123"
        assert payload.token_type == "refresh"

    def test_refresh_token_replay_protection(self, service: JWTService) -> None:
        """Test refresh token can only be used once."""
        token, _ = service.create_refresh_token("user123")

        # First use should succeed
        service.verify_refresh_token(token)

        # Second use should fail
        with pytest.raises(TokenRevokedError, match="already been used"):
            service.verify_refresh_token(token)

    def test_decode_token_unverified(self, service: JWTService) -> None:
        """Test decoding token without verification."""
        token, original = service.create_access_token("user123")

        payload = service.decode_token_unverified(token)

        assert payload.sub == original.sub
        assert payload.jti == original.jti


    def test_clear_used_refresh_tokens(self, service: JWTService) -> None:
        """Test clearing used refresh tokens."""
        token1, _ = service.create_refresh_token("user123")

        # Use the token
        service.verify_refresh_token(token1)

        # Clear tracking
        service.clear_used_refresh_tokens()

        # Create a new token and verify it works
        token2, _ = service.create_refresh_token("user456")
        payload = service.verify_refresh_token(token2)
        assert payload.sub == "user456"


class TestJWTRoundTripProperties:
    """Property-based tests for JWT round-trip.

    **Feature: test-coverage-80-percent-v3, Property 9: JWT Round-trip**
    **Validates: Requirements 4.2**
    """

    SECRET_KEY = "test-secret-key-that-is-at-least-32-characters-long"

    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    )
    @settings(max_examples=50, deadline=5000)
    def test_access_token_round_trip(self, user_id: str) -> None:
        """Property: Access token encodes and decodes correctly.

        **Feature: test-coverage-80-percent-v3, Property 9: JWT Round-trip**
        **Validates: Requirements 4.2**
        """
        service = JWTService(secret_key=self.SECRET_KEY)

        token, original = service.create_access_token(user_id)
        decoded = service.verify_token(token)

        assert decoded.sub == original.sub
        assert decoded.jti == original.jti
        assert decoded.token_type == original.token_type

    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
        scopes=st.lists(st.sampled_from(["read", "write", "admin", "delete"]), max_size=4),
    )
    @settings(max_examples=50, deadline=5000)
    def test_token_with_scopes_round_trip(
        self, user_id: str, scopes: list[str]
    ) -> None:
        """Property: Token with scopes encodes and decodes correctly.

        **Feature: test-coverage-80-percent-v3, Property 9: JWT Round-trip**
        **Validates: Requirements 4.2**
        """
        service = JWTService(secret_key=self.SECRET_KEY)

        token, original = service.create_access_token(user_id, scopes=scopes)
        decoded = service.verify_token(token)

        assert decoded.sub == original.sub
        assert set(decoded.scopes) == set(original.scopes)
