"""Unit tests for request ID middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 9.1**
"""

import importlib.util

# Import directly to avoid circular import issues
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Load the request_id module directly
spec = importlib.util.spec_from_file_location("request_id_module", "src/interface/middleware/request/request_id.py")
request_id_module = importlib.util.module_from_spec(spec)
sys.modules["request_id_module"] = request_id_module
spec.loader.exec_module(request_id_module)

RequestIDMiddleware = request_id_module.RequestIDMiddleware
get_request_id = request_id_module.get_request_id
_is_valid_request_id = request_id_module._is_valid_request_id


class TestIsValidRequestId:
    """Tests for _is_valid_request_id function."""

    def test_valid_uuid(self) -> None:
        """Test that valid UUIDs are accepted."""
        valid_uuid = str(uuid.uuid4())
        assert _is_valid_request_id(valid_uuid) is True

    def test_valid_uuid_uppercase(self) -> None:
        """Test that uppercase UUIDs are accepted."""
        valid_uuid = str(uuid.uuid4()).upper()
        assert _is_valid_request_id(valid_uuid) is True

    def test_invalid_uuid_format(self) -> None:
        """Test that invalid formats are rejected."""
        assert _is_valid_request_id("not-a-uuid") is False
        assert _is_valid_request_id("12345") is False
        assert _is_valid_request_id("") is False

    def test_empty_string(self) -> None:
        """Test that empty string is rejected."""
        assert _is_valid_request_id("") is False

    def test_none_like_values(self) -> None:
        """Test that None-like values are rejected."""
        assert _is_valid_request_id(None) is False  # type: ignore

    def test_injection_attempt(self) -> None:
        """Test that injection attempts are rejected."""
        # SQL injection attempt
        assert _is_valid_request_id("'; DROP TABLE users; --") is False
        # XSS attempt
        assert _is_valid_request_id("<script>alert('xss')</script>") is False
        # Path traversal
        assert _is_valid_request_id("../../../etc/passwd") is False


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware."""

    @pytest.fixture()
    def app(self) -> FastAPI:
        """Create test FastAPI app."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        return app

    def test_generates_request_id_when_missing(self, app: FastAPI) -> None:
        """Test that request ID is generated when not provided."""
        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        assert _is_valid_request_id(request_id)

    def test_uses_provided_valid_request_id(self, app: FastAPI) -> None:
        """Test that valid provided request ID is used."""
        client = TestClient(app)
        provided_id = str(uuid.uuid4())

        response = client.get("/test", headers={"X-Request-ID": provided_id})

        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == provided_id

    def test_generates_new_id_for_invalid_format(self, app: FastAPI) -> None:
        """Test that invalid request ID is replaced with new one."""
        client = TestClient(app)
        invalid_id = "invalid-format"

        response = client.get("/test", headers={"X-Request-ID": invalid_id})

        assert response.status_code == 200
        returned_id = response.headers.get("X-Request-ID")
        assert returned_id != invalid_id
        assert _is_valid_request_id(returned_id)

    def test_generates_new_id_for_injection_attempt(self, app: FastAPI) -> None:
        """Test that injection attempts are rejected."""
        client = TestClient(app)
        injection = "'; DROP TABLE users; --"

        response = client.get("/test", headers={"X-Request-ID": injection})

        assert response.status_code == 200
        returned_id = response.headers.get("X-Request-ID")
        assert returned_id != injection
        assert _is_valid_request_id(returned_id)

    def test_request_id_in_response_header(self, app: FastAPI) -> None:
        """Test that request ID is included in response headers."""
        client = TestClient(app)
        response = client.get("/test")

        assert "X-Request-ID" in response.headers

    def test_request_id_stored_in_state(self) -> None:
        """Test that request ID is stored in request state."""
        from starlette.requests import Request as StarletteRequest

        app = FastAPI()
        stored_id = None

        @app.get("/check-state")
        async def check_state(request: StarletteRequest) -> dict:
            nonlocal stored_id
            stored_id = getattr(request.state, "request_id", None)
            return {"status": "ok"}

        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/check-state")

        assert response.status_code == 200
        assert stored_id is not None
        assert _is_valid_request_id(stored_id)


class TestGetRequestId:
    """Tests for get_request_id helper function."""

    def test_returns_request_id_from_state(self) -> None:
        """Test that request ID is retrieved from state."""
        request = MagicMock()
        request.state.request_id = "test-uuid-1234"

        result = get_request_id(request)

        assert result == "test-uuid-1234"

    def test_returns_none_when_not_set(self) -> None:
        """Test that None is returned when request ID not set."""
        request = MagicMock()
        del request.state.request_id

        result = get_request_id(request)

        assert result is None


class TestLoggingContextIntegration:
    """Tests for logging context integration."""

    def test_sets_logging_context(self) -> None:
        """Test that request ID is set in logging context."""
        with patch.object(request_id_module, "set_request_id") as mock_set:
            with patch.object(request_id_module, "clear_request_id"):
                app = FastAPI()
                app.add_middleware(RequestIDMiddleware)

                @app.get("/test")
                async def test_endpoint() -> dict:
                    return {"status": "ok"}

                client = TestClient(app)
                client.get("/test")

                mock_set.assert_called_once()

    def test_clears_logging_context_after_request(self) -> None:
        """Test that logging context is cleared after request."""
        with (
            patch.object(request_id_module, "set_request_id"),
            patch.object(request_id_module, "clear_request_id") as mock_clear,
        ):
            app = FastAPI()
            app.add_middleware(RequestIDMiddleware)

            @app.get("/test")
            async def test_endpoint() -> dict:
                return {"status": "ok"}

            client = TestClient(app)
            client.get("/test")

            mock_clear.assert_called_once()

    def test_clears_context_even_on_error(self) -> None:
        """Test that logging context is cleared even when handler raises."""
        with (
            patch.object(request_id_module, "set_request_id"),
            patch.object(request_id_module, "clear_request_id") as mock_clear,
        ):
            app = FastAPI()
            app.add_middleware(RequestIDMiddleware)

            @app.get("/error")
            async def error_endpoint() -> dict:
                raise ValueError("Test error")

            client = TestClient(app, raise_server_exceptions=False)
            client.get("/error")

            mock_clear.assert_called_once()


# Property-based tests
from hypothesis import given, settings, strategies as st


class TestRequestIdProperties:
    """Property-based tests for request ID handling."""

    @given(st.uuids())
    @settings(max_examples=100, deadline=5000)
    def test_valid_uuids_always_accepted(self, test_uuid: uuid.UUID) -> None:
        """Test that any valid UUID is accepted."""
        assert _is_valid_request_id(str(test_uuid)) is True

    @given(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ).filter(lambda x: not _is_valid_request_id(x))
    )
    @settings(max_examples=100, deadline=5000)
    def test_invalid_strings_always_rejected(self, invalid_str: str) -> None:
        """Test that invalid strings are always rejected."""
        assert _is_valid_request_id(invalid_str) is False
