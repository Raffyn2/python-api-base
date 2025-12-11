"""Property-based tests for pagination calculations.

**Feature: test-coverage-90-percent, Property 4: Pagination Calculations**
**Validates: Requirements 5.4**
"""

import math
from dataclasses import dataclass

import pytest
from hypothesis import given, settings, strategies as st


@dataclass
class PaginationResult:
    """Result of pagination calculation."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    offset: int
    has_next: bool
    has_prev: bool


def calculate_pagination(page: int, page_size: int, total_items: int) -> PaginationResult:
    """Calculate pagination values.

    Args:
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items

    Returns:
        PaginationResult with calculated values
    """
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    offset = (page - 1) * page_size
    has_next = page < total_pages
    has_prev = page > 1

    return PaginationResult(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        offset=offset,
        has_next=has_next,
        has_prev=has_prev,
    )


@pytest.mark.property
class TestPaginationMathProperties:
    """Property-based tests for pagination calculations.

    **Feature: test-coverage-90-percent, Property 4: Pagination Calculations**
    **Validates: Requirements 5.4**
    """

    @given(total_items=st.integers(min_value=0, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_total_pages_formula(self, total_items: int, page_size: int) -> None:
        """Total pages equals ceil(total_items / page_size).

        Property: total_pages = ceil(total_items / page_size)
        """
        result = calculate_pagination(1, page_size, total_items)

        expected = math.ceil(total_items / page_size) if total_items > 0 else 0

        assert result.total_pages == expected

    @given(page=st.integers(min_value=1, max_value=100), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_offset_formula(self, page: int, page_size: int) -> None:
        """Offset equals (page - 1) * page_size.

        Property: offset = (page - 1) * page_size
        """
        result = calculate_pagination(page, page_size, 1000)

        expected = (page - 1) * page_size

        assert result.offset == expected

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_has_next_on_first_page(self, total_items: int, page_size: int) -> None:
        """First page has_next when total_pages > 1.

        Property: has_next = (page < total_pages)
        """
        result = calculate_pagination(1, page_size, total_items)

        expected = result.total_pages > 1

        assert result.has_next == expected

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_has_prev_on_first_page(self, total_items: int, page_size: int) -> None:
        """First page never has_prev.

        Property: has_prev = (page > 1), so page 1 has_prev = False
        """
        result = calculate_pagination(1, page_size, total_items)

        assert result.has_prev is False

    @given(page=st.integers(min_value=2, max_value=100), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_has_prev_after_first_page(self, page: int, page_size: int) -> None:
        """Pages after first always have has_prev = True.

        Property: has_prev = (page > 1)
        """
        # Ensure enough items for the page to exist
        total_items = page * page_size
        result = calculate_pagination(page, page_size, total_items)

        assert result.has_prev is True

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_last_page_has_no_next(self, total_items: int, page_size: int) -> None:
        """Last page has_next = False.

        Property: On last page, has_next = False
        """
        total_pages = math.ceil(total_items / page_size)
        result = calculate_pagination(total_pages, page_size, total_items)

        assert result.has_next is False

    @given(total_items=st.integers(min_value=0, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_offset_non_negative(self, total_items: int, page_size: int) -> None:
        """Offset is always non-negative.

        Property: offset >= 0
        """
        result = calculate_pagination(1, page_size, total_items)

        assert result.offset >= 0

    @given(total_items=st.integers(min_value=0, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_total_pages_non_negative(self, total_items: int, page_size: int) -> None:
        """Total pages is always non-negative.

        Property: total_pages >= 0
        """
        result = calculate_pagination(1, page_size, total_items)

        assert result.total_pages >= 0

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_total_pages_covers_all_items(self, total_items: int, page_size: int) -> None:
        """Total pages * page_size >= total_items.

        Property: All items fit within total_pages
        """
        result = calculate_pagination(1, page_size, total_items)

        assert result.total_pages * page_size >= total_items

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_total_pages_minimal(self, total_items: int, page_size: int) -> None:
        """Total pages is minimal (one less page wouldn't fit all items).

        Property: (total_pages - 1) * page_size < total_items
        """
        result = calculate_pagination(1, page_size, total_items)

        if result.total_pages > 0:
            assert (result.total_pages - 1) * page_size < total_items

    @given(page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_empty_collection_has_zero_pages(self, page_size: int) -> None:
        """Empty collection has zero total pages.

        Property: total_items = 0 implies total_pages = 0
        """
        result = calculate_pagination(1, page_size, 0)

        assert result.total_pages == 0

    @given(page=st.integers(min_value=1, max_value=50), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_offset_increases_with_page(self, page: int, page_size: int) -> None:
        """Offset increases linearly with page number.

        Property: offset(page+1) - offset(page) = page_size
        """
        total_items = (page + 1) * page_size

        result1 = calculate_pagination(page, page_size, total_items)
        result2 = calculate_pagination(page + 1, page_size, total_items)

        assert result2.offset - result1.offset == page_size

    @given(total_items=st.integers(min_value=1, max_value=10000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_first_page_offset_is_zero(self, total_items: int, page_size: int) -> None:
        """First page always has offset = 0.

        Property: offset(page=1) = 0
        """
        result = calculate_pagination(1, page_size, total_items)

        assert result.offset == 0

    @given(total_items=st.integers(min_value=1, max_value=1000), page_size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_navigation_consistency(self, total_items: int, page_size: int) -> None:
        """Navigation flags are consistent across pages.

        Property: If page N has_next, then page N+1 exists and has_prev
        """
        total_pages = math.ceil(total_items / page_size)

        for page in range(1, min(total_pages, 10) + 1):
            result = calculate_pagination(page, page_size, total_items)

            if result.has_next:
                next_result = calculate_pagination(page + 1, page_size, total_items)
                assert next_result.has_prev is True
