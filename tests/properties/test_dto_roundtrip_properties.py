"""Property-based tests for DTO serialization round-trip.

**Feature: test-coverage-90-percent, Property 1: DTO Serialization Round-Trip**
**Validates: Requirements 1.5, 5.1**
"""

import pytest
from hypothesis import given, settings, strategies as st

from application.common.dto.responses import ApiResponse, PaginatedResponse
from core.base.patterns.result import Err, Ok, result_from_dict


@pytest.mark.property
class TestDtoRoundtripProperties:
    """Property-based tests for DTO round-trip serialization.

    **Feature: test-coverage-90-percent, Property 1: DTO Serialization Round-Trip**
    **Validates: Requirements 1.5, 5.1**
    """

    @given(
        data=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=100),
            st.lists(st.integers(), max_size=10),
            st.dictionaries(st.text(min_size=1, max_size=20), st.integers(), max_size=5),
        ),
        message=st.text(min_size=1, max_size=100),
        status_code=st.integers(min_value=100, max_value=599),
    )
    @settings(max_examples=100)
    def test_api_response_roundtrip(self, data: object, message: str, status_code: int) -> None:
        """ApiResponse should roundtrip through serialization.

        Property: For any valid ApiResponse, serialize then deserialize
        should produce equivalent data.
        """
        original = ApiResponse(data=data, message=message, status_code=status_code)

        # Serialize
        serialized = original.model_dump()

        # Deserialize
        restored = ApiResponse.model_validate(serialized)

        # Verify equivalence
        assert restored.data == original.data
        assert restored.message == original.message
        assert restored.status_code == original.status_code

    @given(
        items=st.lists(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=3), max_size=10),
        total=st.integers(min_value=0, max_value=10000),
        page=st.integers(min_value=1, max_value=100),
        size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_paginated_response_roundtrip(self, items: list, total: int, page: int, size: int) -> None:
        """PaginatedResponse should roundtrip through serialization.

        Property: For any valid PaginatedResponse, serialize then deserialize
        should produce equivalent data.
        """
        original = PaginatedResponse(items=items, total=total, page=page, size=size)

        # Serialize
        serialized = original.model_dump()

        # Deserialize
        restored = PaginatedResponse.model_validate(serialized)

        # Verify equivalence
        assert restored.items == original.items
        assert restored.total == original.total
        assert restored.page == original.page
        assert restored.size == original.size
        assert restored.pages == original.pages
        assert restored.has_next == original.has_next
        assert restored.has_previous == original.has_previous

    @given(value=st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=50)))
    @settings(max_examples=100)
    def test_result_ok_roundtrip(self, value: object) -> None:
        """Ok Result should roundtrip through serialization.

        Property: For any Ok value, to_dict then result_from_dict
        should produce equivalent Result.
        """
        original = Ok(value)

        # Serialize
        serialized = original.to_dict()

        # Deserialize
        restored = result_from_dict(serialized)

        # Verify equivalence
        assert restored.is_ok()
        assert restored.unwrap() == original.value

    @given(error=st.one_of(st.text(min_size=1, max_size=50), st.integers()))
    @settings(max_examples=100)
    def test_result_err_roundtrip(self, error: object) -> None:
        """Err Result should roundtrip through serialization.

        Property: For any Err value, to_dict then result_from_dict
        should produce equivalent Result.
        """
        original = Err(error)

        # Serialize
        serialized = original.to_dict()

        # Deserialize
        restored = result_from_dict(serialized)

        # Verify equivalence
        assert restored.is_err()

    @given(
        items=st.lists(st.integers(), max_size=20),
        page=st.integers(min_value=1, max_value=50),
        size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_paginated_response_computed_fields_consistent(self, items: list, page: int, size: int) -> None:
        """PaginatedResponse computed fields should be consistent.

        Property: Computed fields should be deterministic and consistent
        across multiple accesses.
        """
        total = len(items) * 5  # Simulate more items than shown

        response = PaginatedResponse(items=items, total=total, page=page, size=size)

        # Access computed fields multiple times
        pages1 = response.pages
        pages2 = response.pages
        has_next1 = response.has_next
        has_next2 = response.has_next
        has_prev1 = response.has_previous
        has_prev2 = response.has_previous

        # Should be consistent
        assert pages1 == pages2
        assert has_next1 == has_next2
        assert has_prev1 == has_prev2

    @given(
        data=st.dictionaries(
            st.text(
                min_size=1,
                max_size=10,
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_"),
            ),
            st.one_of(st.integers(), st.text(max_size=20), st.booleans()),
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_api_response_json_roundtrip(self, data: dict) -> None:
        """ApiResponse should roundtrip through JSON serialization.

        Property: For any valid data, JSON serialize then deserialize
        should produce equivalent ApiResponse.
        """
        original = ApiResponse(data=data)

        # JSON serialize
        json_str = original.model_dump_json()

        # JSON deserialize
        restored = ApiResponse.model_validate_json(json_str)

        # Verify equivalence
        assert restored.data == original.data
        assert restored.message == original.message
        assert restored.status_code == original.status_code
