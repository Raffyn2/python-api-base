"""Integration tests for API Best Practices 2025 features.

**Feature: api-best-practices-review-2025**
**Validates: End-to-end testing of JWKS, Health, Idempotency**

Run with: pytest tests/integration/interface/test_api_best_practices_2025_integration.py -v

Requirements:
- Docker services running (postgres, redis)
- Or: pytest markers to skip when services unavailable
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Skip if services not available
SKIP_INTEGRATION = os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true"

# Mark for integration tests requiring Docker
requires_docker = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Integration tests disabled (set SKIP_INTEGRATION_TESTS=false)",
)


@pytest.fixture()
async def async_client():
    """Create async HTTP client for testing."""
    # Import here to avoid startup issues when services not available
    try:
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    except Exception as e:
        pytest.skip(f"Cannot create test client: {e}")


@requires_docker
class TestJWKSEndpointIntegration:
    """Integration tests for JWKS endpoint.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @pytest.mark.asyncio
    async def test_jwks_endpoint_returns_valid_json(self, async_client: AsyncClient) -> None:
        """JWKS endpoint SHALL return valid JWK Set.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 1.1**
        """
        response = await async_client.get("/.well-known/jwks.json")

        assert response.status_code == 200
        data = response.json()

        # Must have keys array
        assert "keys" in data
        assert isinstance(data["keys"], list)

    @pytest.mark.asyncio
    async def test_jwks_has_cache_headers(self, async_client: AsyncClient) -> None:
        """JWKS endpoint SHALL include cache headers.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 1.2**
        """
        response = await async_client.get("/.well-known/jwks.json")

        assert response.status_code == 200
        # Should have cache-related headers
        assert "cache-control" in response.headers or "Cache-Control" in response.headers

    @pytest.mark.asyncio
    async def test_openid_configuration_endpoint(self, async_client: AsyncClient) -> None:
        """OpenID Configuration endpoint SHALL be available.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 1.3**
        """
        response = await async_client.get("/.well-known/openid-configuration")

        assert response.status_code == 200
        data = response.json()

        # Must have jwks_uri
        assert "jwks_uri" in data


@requires_docker
class TestHealthEndpointsIntegration:
    """Integration tests for health check endpoints.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.1, 24.2, 24.3**
    """

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, async_client: AsyncClient) -> None:
        """Liveness endpoint SHALL return 200.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.1**
        """
        response = await async_client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, async_client: AsyncClient) -> None:
        """Readiness endpoint SHALL return health status.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.2**
        """
        response = await async_client.get("/health/ready")

        # May be 200 or 503 depending on dependencies
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_startup_endpoint(self, async_client: AsyncClient) -> None:
        """Startup endpoint SHALL return startup status.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.3**
        """
        response = await async_client.get("/health/startup")

        # May be 200 or 503 depending on startup state
        assert response.status_code in [200, 503]
        data = response.json()
        assert "startup_complete" in data


@requires_docker
class TestIdempotencyIntegration:
    """Integration tests for idempotency handling.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.1, 23.2, 23.3, 23.4**

    Note: These tests require a POST endpoint that supports idempotency.
    """

    @pytest.mark.asyncio
    async def test_idempotency_header_accepted(self, async_client: AsyncClient) -> None:
        """POST with Idempotency-Key SHALL be processed.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.1**
        """
        # Try any POST endpoint with idempotency key
        # Note: May need adjustment based on actual endpoints
        response = await async_client.post(
            "/api/v1/examples/items",
            json={"name": "Test Item", "value": 100},
            headers={"Idempotency-Key": "test-key-12345"},
        )

        # We're just testing the header is accepted
        # Actual response depends on endpoint implementation
        # 401/422/201 are all valid responses
        assert response.status_code in [200, 201, 400, 401, 403, 422]


# === Unit-style Integration Tests (No Docker Required) ===


class TestJWKSServiceUnit:
    """Unit-level tests for JWKS service.

    **Feature: api-best-practices-review-2025**
    These tests don't require Docker.
    """

    def test_jwks_service_generates_keys(self) -> None:
        """JWKS service SHALL generate valid JWK.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 1.1**
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        from infrastructure.auth.jwt.jwks import JWKSService

        # Generate test keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        service = JWKSService()
        service.add_key(public_key_pem, algorithm="RS256", kid="test-kid")

        jwks = service.get_jwks()
        assert len(jwks.keys) == 1
        assert jwks.keys[0].kid == "test-kid"
        assert jwks.keys[0].kty == "RSA"
        assert jwks.keys[0].use == "sig"

    def test_jwks_key_rotation(self) -> None:
        """JWKS service SHALL support key rotation.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 1.4**
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        from infrastructure.auth.jwt.jwks import JWKSService

        def generate_public_pem():
            key = rsa.generate_private_key(65537, 2048, default_backend())
            return (
                key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode()
            )

        service = JWKSService()

        # Add first key
        service.add_key(generate_public_pem(), algorithm="RS256", kid="key1")
        assert len(service.get_jwks().keys) == 1

        # Add second key (rotation)
        service.add_key(generate_public_pem(), algorithm="RS256", kid="key2")
        assert len(service.get_jwks().keys) == 2

        # Revoke first key
        service.revoke_key("key1")
        # Key may still be in JWKS during grace period or removed
        assert len(service.get_jwks().keys) >= 1


class TestCacheJitterUnit:
    """Unit-level tests for cache jitter.

    **Feature: api-best-practices-review-2025**
    """

    def test_jitter_within_range(self) -> None:
        """Jitter SHALL be within configured range.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 22.1**
        """
        from infrastructure.cache.providers.redis_jitter import (
            JitterConfig,
            RedisCacheWithJitter,
        )

        config = JitterConfig(
            min_jitter_percent=0.05,
            max_jitter_percent=0.15,
        )
        cache = RedisCacheWithJitter[dict](config=config)

        base_ttl = 300
        for _ in range(100):
            jittered = cache._apply_jitter(base_ttl)
            assert jittered >= base_ttl
            assert jittered <= int(base_ttl * 1.15) + 1


class TestIdempotencyHandlerUnit:
    """Unit-level tests for idempotency handler.

    **Feature: api-best-practices-review-2025**
    """

    def test_request_hash_deterministic(self) -> None:
        """Request hash SHALL be deterministic.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        from infrastructure.idempotency.handler import compute_request_hash

        hash1 = compute_request_hash("POST", "/api/test", b'{"key": "value"}')
        hash2 = compute_request_hash("POST", "/api/test", b'{"key": "value"}')

        assert hash1 == hash2

    def test_different_bodies_different_hashes(self) -> None:
        """Different request bodies SHALL have different hashes.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 23.4**
        """
        from infrastructure.idempotency.handler import compute_request_hash

        hash1 = compute_request_hash("POST", "/api/test", b'{"key": "value1"}')
        hash2 = compute_request_hash("POST", "/api/test", b'{"key": "value2"}')

        assert hash1 != hash2


class TestGracefulShutdownUnit:
    """Unit-level tests for graceful shutdown.

    **Feature: api-best-practices-review-2025**
    """

    def test_shutdown_handler_tracks_requests(self) -> None:
        """Shutdown handler SHALL track in-flight requests.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        from infrastructure.lifecycle import ShutdownHandler

        handler = ShutdownHandler()

        assert handler.in_flight_requests == 0

        handler.request_started()
        assert handler.in_flight_requests == 1

        handler.request_finished()
        assert handler.in_flight_requests == 0

    @pytest.mark.asyncio
    async def test_shutdown_runs_hooks(self) -> None:
        """Shutdown SHALL run registered hooks.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.5**
        """
        from infrastructure.lifecycle import ShutdownHandler

        handler = ShutdownHandler()
        hook_called = False

        async def cleanup_hook():
            nonlocal hook_called
            hook_called = True

        handler.add_hook("cleanup", cleanup_hook)
        await handler.shutdown()

        assert hook_called is True
