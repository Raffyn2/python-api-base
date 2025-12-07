"""Unit tests for batch interfaces and utilities.

Tests chunk_sequence and iter_chunks functions.
"""

import pytest

from application.common.batch import chunk_sequence, iter_chunks


class TestChunkSequence:
    """Tests for chunk_sequence function."""

    def test_exact_chunks(self) -> None:
        """Test sequence that divides evenly."""
        items = [1, 2, 3, 4, 5, 6]
        chunks = chunk_sequence(items, 2)
        assert len(chunks) == 3
        assert list(chunks[0]) == [1, 2]
        assert list(chunks[1]) == [3, 4]
        assert list(chunks[2]) == [5, 6]

    def test_remainder_chunk(self) -> None:
        """Test sequence with remainder."""
        items = [1, 2, 3, 4, 5]
        chunks = chunk_sequence(items, 2)
        assert len(chunks) == 3
        assert list(chunks[0]) == [1, 2]
        assert list(chunks[1]) == [3, 4]
        assert list(chunks[2]) == [5]

    def test_single_chunk(self) -> None:
        """Test sequence smaller than chunk size."""
        items = [1, 2, 3]
        chunks = chunk_sequence(items, 10)
        assert len(chunks) == 1
        assert list(chunks[0]) == [1, 2, 3]

    def test_empty_sequence(self) -> None:
        """Test empty sequence."""
        items: list[int] = []
        chunks = chunk_sequence(items, 5)
        assert len(chunks) == 0

    def test_chunk_size_one(self) -> None:
        """Test chunk size of one."""
        items = [1, 2, 3]
        chunks = chunk_sequence(items, 1)
        assert len(chunks) == 3
        assert list(chunks[0]) == [1]
        assert list(chunks[1]) == [2]
        assert list(chunks[2]) == [3]

    def test_invalid_chunk_size_zero(self) -> None:
        """Test zero chunk size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_sequence([1, 2, 3], 0)

    def test_invalid_chunk_size_negative(self) -> None:
        """Test negative chunk size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_sequence([1, 2, 3], -1)

    def test_string_sequence(self) -> None:
        """Test chunking string sequence."""
        items = ["a", "b", "c", "d", "e"]
        chunks = chunk_sequence(items, 2)
        assert len(chunks) == 3
        assert list(chunks[0]) == ["a", "b"]

    def test_tuple_sequence(self) -> None:
        """Test chunking tuple sequence."""
        items = (1, 2, 3, 4)
        chunks = chunk_sequence(items, 2)
        assert len(chunks) == 2


class TestIterChunks:
    """Tests for iter_chunks async generator."""

    @pytest.mark.asyncio
    async def test_iterate_chunks(self) -> None:
        """Test iterating over chunks."""
        items = [1, 2, 3, 4, 5]
        results = []
        async for idx, chunk in iter_chunks(items, 2):
            results.append((idx, list(chunk)))

        assert len(results) == 3
        assert results[0] == (0, [1, 2])
        assert results[1] == (1, [3, 4])
        assert results[2] == (2, [5])

    @pytest.mark.asyncio
    async def test_iterate_empty(self) -> None:
        """Test iterating over empty sequence."""
        items: list[int] = []
        results = []
        async for idx, chunk in iter_chunks(items, 2):
            results.append((idx, list(chunk)))

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_iterate_single_chunk(self) -> None:
        """Test iterating with single chunk."""
        items = [1, 2]
        results = []
        async for idx, chunk in iter_chunks(items, 10):
            results.append((idx, list(chunk)))

        assert len(results) == 1
        assert results[0] == (0, [1, 2])
