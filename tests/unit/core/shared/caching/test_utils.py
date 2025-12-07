"""Tests for caching utilities.

**Feature: realistic-test-coverage**
**Validates: Requirements 5.5**
"""

import pytest

from core.shared.caching.utils import generate_cache_key


def sample_function(a: int, b: str) -> str:
    """Sample function for testing."""
    return f"{a}-{b}"


def another_function(x: int) -> int:
    """Another sample function."""
    return x * 2


class TestGenerateCacheKey:
    """Tests for generate_cache_key function."""

    def test_generates_string_key(self) -> None:
        """Test that function generates a string key."""
        key = generate_cache_key(sample_function, (1, "test"), {})
        assert isinstance(key, str)

    def test_key_length(self) -> None:
        """Test that key has expected length (32 chars)."""
        key = generate_cache_key(sample_function, (1, "test"), {})
        assert len(key) == 32

    def test_same_args_same_key(self) -> None:
        """Test that same arguments produce same key."""
        key1 = generate_cache_key(sample_function, (1, "test"), {})
        key2 = generate_cache_key(sample_function, (1, "test"), {})
        assert key1 == key2

    def test_different_args_different_key(self) -> None:
        """Test that different arguments produce different keys."""
        key1 = generate_cache_key(sample_function, (1, "test"), {})
        key2 = generate_cache_key(sample_function, (2, "test"), {})
        assert key1 != key2

    def test_different_functions_different_key(self) -> None:
        """Test that different functions produce different keys."""
        key1 = generate_cache_key(sample_function, (1,), {})
        key2 = generate_cache_key(another_function, (1,), {})
        assert key1 != key2

    def test_with_kwargs(self) -> None:
        """Test key generation with keyword arguments."""
        key = generate_cache_key(sample_function, (), {"a": 1, "b": "test"})
        assert isinstance(key, str)
        assert len(key) == 32

    def test_kwargs_order_independent(self) -> None:
        """Test that kwargs order doesn't affect key."""
        key1 = generate_cache_key(sample_function, (), {"a": 1, "b": "test"})
        key2 = generate_cache_key(sample_function, (), {"b": "test", "a": 1})
        assert key1 == key2

    def test_mixed_args_and_kwargs(self) -> None:
        """Test key generation with both args and kwargs."""
        key = generate_cache_key(sample_function, (1,), {"b": "test"})
        assert isinstance(key, str)

    def test_with_none_values(self) -> None:
        """Test key generation with None values."""
        key = generate_cache_key(sample_function, (None, None), {})
        assert isinstance(key, str)

    def test_with_complex_types(self) -> None:
        """Test key generation with complex types."""
        key = generate_cache_key(
            sample_function,
            ([1, 2, 3], {"nested": "dict"}),
            {},
        )
        assert isinstance(key, str)

    def test_with_empty_args(self) -> None:
        """Test key generation with empty arguments."""
        key = generate_cache_key(sample_function, (), {})
        assert isinstance(key, str)

    def test_key_is_hexadecimal(self) -> None:
        """Test that key contains only hexadecimal characters."""
        key = generate_cache_key(sample_function, (1, "test"), {})
        assert all(c in "0123456789abcdef" for c in key)

    def test_with_lambda(self) -> None:
        """Test key generation with lambda function."""
        func = lambda x: x * 2
        key = generate_cache_key(func, (5,), {})
        assert isinstance(key, str)

    def test_with_class_method(self) -> None:
        """Test key generation with class method."""

        class MyClass:
            def method(self, x: int) -> int:
                return x

        obj = MyClass()
        key = generate_cache_key(obj.method, (10,), {})
        assert isinstance(key, str)

    def test_with_boolean_args(self) -> None:
        """Test key generation with boolean arguments."""
        key1 = generate_cache_key(sample_function, (True,), {})
        key2 = generate_cache_key(sample_function, (False,), {})
        assert key1 != key2

    def test_with_float_args(self) -> None:
        """Test key generation with float arguments."""
        key = generate_cache_key(sample_function, (3.14, 2.71), {})
        assert isinstance(key, str)

    def test_with_tuple_args(self) -> None:
        """Test key generation with tuple arguments."""
        key = generate_cache_key(sample_function, ((1, 2, 3),), {})
        assert isinstance(key, str)
