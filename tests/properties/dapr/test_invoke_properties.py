"""Property-based tests for Dapr service invocation.

These tests verify correctness properties for service invocation operations.
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.dapr.invoke import ServiceInvoker, HttpMethod, InvocationResponse


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock Dapr client."""
    client = MagicMock()
    client.http_client = AsyncMock()
    client.settings = MagicMock()
    client.settings.timeout_seconds = 60
    return client


@pytest.fixture
def service_invoker(mock_client: MagicMock) -> ServiceInvoker:
    """Create a ServiceInvoker with mock client."""
    return ServiceInvoker(mock_client)


class TestServiceInvocationHttpMethods:
    """
    **Feature: dapr-sidecar-integration, Property 8: Service Invocation HTTP Method Support**
    **Validates: Requirements 2.3**

    For any HTTP method (GET, POST, PUT, DELETE, PATCH), service invocation
    should correctly send the request with the specified method and headers.
    """

    @given(
        http_method=st.sampled_from([HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE, HttpMethod.PATCH]),
        app_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
        method_name=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_/"
        )).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_http_method_support(
        self,
        mock_client: MagicMock,
        http_method: HttpMethod,
        app_id: str,
        method_name: str,
    ) -> None:
        """All HTTP methods should be supported correctly."""
        mock_response = MagicMock()
        mock_response.content = b'{"result": "success"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_client.http_client.request = AsyncMock(return_value=mock_response)
        
        invoker = ServiceInvoker(mock_client)
        response = await invoker.invoke(
            app_id=app_id,
            method_name=method_name,
            http_verb=http_method,
        )
        
        assert response.status_code == 200
        mock_client.http_client.request.assert_called_once()
        call_kwargs = mock_client.http_client.request.call_args.kwargs
        assert call_kwargs["method"] == http_method.value

    @given(
        headers=st.dictionaries(
            st.text(min_size=1, max_size=30, alphabet=st.characters(
                whitelist_categories=("L", "N"),
                whitelist_characters="-_"
            )).filter(lambda x: x.strip()),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_custom_headers_propagation(
        self,
        mock_client: MagicMock,
        headers: dict[str, str],
    ) -> None:
        """Custom headers should be propagated to the request."""
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_client.http_client.request = AsyncMock(return_value=mock_response)
        
        invoker = ServiceInvoker(mock_client)
        await invoker.invoke(
            app_id="test-service",
            method_name="test-method",
            headers=headers,
        )
        
        call_kwargs = mock_client.http_client.request.call_args.kwargs
        for key, value in headers.items():
            assert call_kwargs["headers"].get(key) == value


class TestTraceContextPropagation:
    """
    **Feature: dapr-sidecar-integration, Property 9: Trace Context Propagation**
    **Validates: Requirements 2.5, 10.1**

    For any service invocation with tracing enabled, the traceparent and
    tracestate headers should be present in the outgoing request.
    """

    @given(
        app_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
        method_name=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_/"
        )).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_trace_headers_added(
        self,
        mock_client: MagicMock,
        app_id: str,
        method_name: str,
    ) -> None:
        """Trace context headers should be added when tracing is enabled."""
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_client.http_client.request = AsyncMock(return_value=mock_response)
        
        invoker = ServiceInvoker(mock_client)
        
        with patch.object(invoker, '_get_trace_headers', return_value={
            "traceparent": "00-trace-id-span-id-01",
            "tracestate": "key=value",
        }):
            await invoker.invoke(app_id=app_id, method_name=method_name)
        
        call_kwargs = mock_client.http_client.request.call_args.kwargs
        assert "traceparent" in call_kwargs["headers"]
        assert "tracestate" in call_kwargs["headers"]

    @given(
        data=st.binary(min_size=1, max_size=1000),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_request_body_propagation(
        self,
        mock_client: MagicMock,
        data: bytes,
    ) -> None:
        """Request body should be propagated correctly."""
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_client.http_client.request = AsyncMock(return_value=mock_response)
        
        invoker = ServiceInvoker(mock_client)
        await invoker.invoke(
            app_id="test-service",
            method_name="test-method",
            data=data,
            http_verb=HttpMethod.POST,
        )
        
        call_kwargs = mock_client.http_client.request.call_args.kwargs
        assert call_kwargs["content"] == data
