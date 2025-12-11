"""Property-based tests for DTO serialization.

**Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
**Validates: Requirements 4.2, 5.3, 7.1**
"""

from hypothesis import given, settings, strategies as st

from application.common.dto import (
    ApiResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    PaginatedResponse,
    ProblemDetail,
)


class TestDTOSerializationProperties:
    """Property-based tests for DTO serialization round-trip."""

    @given(
        data=st.text(min_size=0, max_size=100),
        message=st.text(min_size=1, max_size=50),
        status_code=st.integers(min_value=100, max_value=599),
    )
    @settings(max_examples=100)
    def test_api_response_roundtrip(self, data: str, message: str, status_code: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2, 5.3, 7.1**

        For any ApiResponse, serializing to JSON and deserializing back
        SHALL produce an equivalent object.
        """
        original = ApiResponse[str](
            data=data,
            message=message,
            status_code=status_code,
        )
        json_str = original.model_dump_json()
        restored = ApiResponse[str].model_validate_json(json_str)

        assert restored.data == original.data
        assert restored.message == original.message
        assert restored.status_code == original.status_code

    @given(
        items=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10),
        total=st.integers(min_value=0, max_value=10000),
        page=st.integers(min_value=1, max_value=1000),
        size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_paginated_response_roundtrip(self, items: list, total: int, page: int, size: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2, 5.3, 7.1**

        For any PaginatedResponse, serializing to JSON and deserializing back
        SHALL produce an equivalent object.
        """
        original = PaginatedResponse[str](
            items=items,
            total=total,
            page=page,
            size=size,
        )
        json_str = original.model_dump_json()
        restored = PaginatedResponse[str].model_validate_json(json_str)

        assert restored.items == original.items
        assert restored.total == original.total
        assert restored.page == original.page
        assert restored.size == original.size

    @given(
        ids=st.lists(
            st.text(
                min_size=1,
                max_size=36,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=100)
    def test_bulk_delete_request_roundtrip(self, ids: list) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2, 5.3, 7.1**

        For any BulkDeleteRequest, serializing to JSON and deserializing back
        SHALL produce an equivalent object.
        """
        original = BulkDeleteRequest(ids=ids)
        json_str = original.model_dump_json()
        restored = BulkDeleteRequest.model_validate_json(json_str)

        assert restored.ids == original.ids

    @given(
        deleted_count=st.integers(min_value=0, max_value=1000),
        failed_ids=st.lists(st.text(min_size=1, max_size=36), min_size=0, max_size=10),
    )
    @settings(max_examples=100)
    def test_bulk_delete_response_roundtrip(self, deleted_count: int, failed_ids: list) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2, 5.3, 7.1**

        For any BulkDeleteResponse, serializing to JSON and deserializing back
        SHALL produce an equivalent object.
        """
        original = BulkDeleteResponse(
            deleted_count=deleted_count,
            failed_ids=failed_ids,
        )
        json_str = original.model_dump_json()
        restored = BulkDeleteResponse.model_validate_json(json_str)

        assert restored.deleted_count == original.deleted_count
        assert restored.failed_ids == original.failed_ids

    @given(
        title=st.text(min_size=1, max_size=100),
        status=st.integers(min_value=100, max_value=599),
        detail=st.text(min_size=0, max_size=200) | st.none(),
    )
    @settings(max_examples=100)
    def test_problem_detail_roundtrip(self, title: str, status: int, detail: str | None) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2, 5.3, 7.1**

        For any ProblemDetail, serializing to JSON and deserializing back
        SHALL produce an equivalent object.
        """
        original = ProblemDetail(
            title=title,
            status=status,
            detail=detail,
        )
        json_str = original.model_dump_json()
        restored = ProblemDetail.model_validate_json(json_str)

        assert restored.title == original.title
        assert restored.status == original.status
        assert restored.detail == original.detail


class TestPaginationProperties:
    """Property-based tests for pagination computed fields."""

    @given(
        total=st.integers(min_value=1, max_value=10000),
        size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pages_calculation_correct(self, total: int, size: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2**

        For any total and size, pages SHALL equal ceil(total / size).
        """
        response = PaginatedResponse[str](
            items=[],
            total=total,
            page=1,
            size=size,
        )
        expected_pages = (total + size - 1) // size
        assert response.pages == expected_pages

    @given(
        total=st.integers(min_value=1, max_value=1000),
        size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_has_next_on_last_page_false(self, total: int, size: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2**

        On the last page, has_next SHALL be False.
        """
        pages = (total + size - 1) // size
        response = PaginatedResponse[str](
            items=[],
            total=total,
            page=pages,
            size=size,
        )
        assert response.has_next is False

    @given(page=st.integers(min_value=2, max_value=1000))
    @settings(max_examples=100)
    def test_has_previous_on_page_gt_1_true(self, page: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 1: Serialization Round-Trip**
        **Validates: Requirements 4.2**

        On any page > 1, has_previous SHALL be True.
        """
        response = PaginatedResponse[str](
            items=[],
            total=page * 10,
            page=page,
            size=10,
        )
        assert response.has_previous is True
