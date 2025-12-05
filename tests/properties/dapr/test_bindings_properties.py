"""Property-based tests for Dapr bindings.

These tests verify correctness properties for binding operations.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import AsyncMock, MagicMock

from infrastructure.dapr.bindings import BindingsManager, InputBindingEvent


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock Dapr client."""
    client = MagicMock()
    client.http_client = AsyncMock()
    return client


@pytest.fixture
def bindings_manager(mock_client: MagicMock) -> BindingsManager:
    """Create a BindingsManager with mock client."""
    return BindingsManager(mock_client)


class TestBindingOperations:
    """
    Unit tests for binding operations.
    **Validates: Requirements 6.3, 6.4, 6.5**
    """

    @given(
        binding_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
        operation=st.sampled_from(["create", "get", "delete", "list"]),
        data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=("L", "N"),
            )),
            st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_output_binding_invocation(
        self,
        mock_client: MagicMock,
        binding_name: str,
        operation: str,
        data: dict,
    ) -> None:
        """Output bindings should be invoked with correct parameters."""
        mock_response = MagicMock()
        mock_response.content = b'{"success": true}'
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}
        mock_client.http_client.post = AsyncMock(return_value=mock_response)
        
        manager = BindingsManager(mock_client)
        response = await manager.invoke_binding(
            binding_name=binding_name,
            operation=operation,
            data=data,
        )
        
        assert response.data is not None
        mock_client.http_client.post.assert_called_once()
        call_args = mock_client.http_client.post.call_args
        assert f"/v1.0/bindings/{binding_name}" in call_args[0][0]

    @given(
        binding_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=("L", "N"),
            )),
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_binding_metadata_propagation(
        self,
        mock_client: MagicMock,
        binding_name: str,
        metadata: dict[str, str],
    ) -> None:
        """Binding metadata should be propagated correctly."""
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}
        mock_client.http_client.post = AsyncMock(return_value=mock_response)
        
        manager = BindingsManager(mock_client)
        await manager.invoke_binding(
            binding_name=binding_name,
            operation="create",
            metadata=metadata,
        )
        
        call_args = mock_client.http_client.post.call_args
        payload = json.loads(call_args.kwargs["content"])
        assert payload.get("metadata") == metadata

    @given(
        binding_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_input_binding_handler_registration(
        self,
        mock_client: MagicMock,
        binding_name: str,
    ) -> None:
        """Input binding handlers should be registered correctly."""
        manager = BindingsManager(mock_client)
        
        async def handler(event: InputBindingEvent) -> dict | None:
            return {"processed": True}
        
        manager.register_handler(binding_name, handler)
        
        assert binding_name in manager.get_registered_bindings()

    @given(
        binding_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
        data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=("L", "N"),
            )),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_input_binding_event_handling(
        self,
        mock_client: MagicMock,
        binding_name: str,
        data: dict,
    ) -> None:
        """Input binding events should be handled correctly."""
        manager = BindingsManager(mock_client)
        received_data = None
        
        async def handler(event: InputBindingEvent) -> dict | None:
            nonlocal received_data
            received_data = event.data
            return {"processed": True}
        
        manager.register_handler(binding_name, handler)
        result = await manager.handle_event(binding_name, data)
        
        assert received_data == data
        assert result == {"processed": True}

    @given(
        binding_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="-_"
        )).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_unregistered_binding_returns_none(
        self,
        mock_client: MagicMock,
        binding_name: str,
    ) -> None:
        """Unregistered bindings should return None."""
        manager = BindingsManager(mock_client)
        result = await manager.handle_event(binding_name, {"test": "data"})
        
        assert result is None
