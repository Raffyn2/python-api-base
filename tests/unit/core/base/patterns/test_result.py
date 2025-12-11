"""Tests for core/base/patterns/result.py - Result pattern."""

import pytest

from src.core.base.patterns.result import (
    Err,
    Ok,
    collect_results,
    err,
    ok,
    result_from_dict,
    try_catch,
)


class TestOk:
    """Tests for Ok class."""

    def test_is_ok_returns_true(self):
        result = Ok(42)
        assert result.is_ok() is True

    def test_is_err_returns_false(self):
        result = Ok(42)
        assert result.is_err() is False

    def test_unwrap_returns_value(self):
        result = Ok(42)
        assert result.unwrap() == 42

    def test_unwrap_or_returns_value(self):
        result = Ok(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_else_returns_value(self):
        result = Ok(42)
        assert result.unwrap_or_else(lambda: 0) == 42

    def test_expect_returns_value(self):
        result = Ok(42)
        assert result.expect("Should not fail") == 42

    def test_map_transforms_value(self):
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 20

    def test_map_returns_ok(self):
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert isinstance(mapped, Ok)

    def test_bind_chains_operations(self):
        result = Ok(10)
        chained = result.bind(lambda x: Ok(x * 2))
        assert chained.unwrap() == 20

    def test_and_then_chains_operations(self):
        result = Ok(10)
        chained = result.and_then(lambda x: Ok(x + 5))
        assert chained.unwrap() == 15

    def test_or_else_returns_self(self):
        result = Ok(42)
        handled = result.or_else(lambda _: Ok(0))
        assert handled.unwrap() == 42

    def test_map_err_returns_self(self):
        result = Ok(42)
        mapped = result.map_err(lambda e: str(e))
        assert mapped.unwrap() == 42

    def test_match_calls_on_ok(self):
        result = Ok(42)
        matched = result.match(
            on_ok=lambda x: x * 2,
            on_err=lambda e: 0,
        )
        assert matched == 84

    def test_inspect_calls_function(self):
        result = Ok(42)
        called = []
        result.inspect(lambda x: called.append(x))
        assert called == [42]

    def test_inspect_returns_self(self):
        result = Ok(42)
        returned = result.inspect(lambda x: None)
        assert returned is result

    def test_inspect_err_does_nothing(self):
        result = Ok(42)
        called = []
        result.inspect_err(lambda e: called.append(e))
        assert called == []

    def test_to_dict(self):
        result = Ok(42)
        d = result.to_dict()
        assert d == {"type": "Ok", "value": 42}


class TestErr:
    """Tests for Err class."""

    def test_is_ok_returns_false(self):
        result = Err("error")
        assert result.is_ok() is False

    def test_is_err_returns_true(self):
        result = Err("error")
        assert result.is_err() is True

    def test_unwrap_raises(self):
        result = Err("error")
        with pytest.raises(ValueError):
            result.unwrap()

    def test_unwrap_or_returns_default(self):
        result = Err("error")
        assert result.unwrap_or(42) == 42

    def test_unwrap_or_else_calls_function(self):
        result = Err("error")
        assert result.unwrap_or_else(lambda e: len(e)) == 5

    def test_expect_raises_with_message(self):
        result = Err("error")
        with pytest.raises(ValueError, match="Custom message"):
            result.expect("Custom message")

    def test_map_returns_self(self):
        result = Err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.error == "error"

    def test_bind_returns_self(self):
        result = Err("error")
        chained = result.bind(lambda x: Ok(x * 2))
        assert chained.is_err()

    def test_and_then_returns_self(self):
        result = Err("error")
        chained = result.and_then(lambda x: Ok(x + 5))
        assert chained.is_err()

    def test_or_else_calls_function(self):
        result = Err("error")
        handled = result.or_else(lambda e: Ok(len(e)))
        assert handled.unwrap() == 5

    def test_map_err_transforms_error(self):
        result = Err("error")
        mapped = result.map_err(lambda e: e.upper())
        assert mapped.error == "ERROR"

    def test_match_calls_on_err(self):
        result = Err("error")
        matched = result.match(
            on_ok=lambda x: x * 2,
            on_err=lambda e: len(e),
        )
        assert matched == 5

    def test_inspect_does_nothing(self):
        result = Err("error")
        called = []
        result.inspect(lambda x: called.append(x))
        assert called == []

    def test_inspect_err_calls_function(self):
        result = Err("error")
        called = []
        result.inspect_err(lambda e: called.append(e))
        assert called == ["error"]

    def test_inspect_err_returns_self(self):
        result = Err("error")
        returned = result.inspect_err(lambda e: None)
        assert returned is result

    def test_to_dict(self):
        result = Err("error")
        d = result.to_dict()
        assert d == {"type": "Err", "error": "error"}

    def test_flatten_returns_self(self):
        result = Err("error")
        flattened = result.flatten()
        assert flattened is result


class TestOkFlatten:
    """Tests for Ok.flatten method."""

    def test_flatten_nested_ok(self):
        result = Ok(Ok(42))
        flattened = result.flatten()
        assert flattened.unwrap() == 42

    def test_flatten_nested_err(self):
        result = Ok(Err("error"))
        flattened = result.flatten()
        assert flattened.is_err()


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_ok_creates_ok(self):
        result = ok(42)
        assert isinstance(result, Ok)
        assert result.unwrap() == 42

    def test_err_creates_err(self):
        result = err("error")
        assert isinstance(result, Err)
        assert result.error == "error"


class TestTryCatch:
    """Tests for try_catch function."""

    def test_try_catch_success(self):
        result = try_catch(lambda: 42)
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_try_catch_failure(self):
        result = try_catch(lambda: 1 / 0, ZeroDivisionError)
        assert result.is_err()
        assert isinstance(result.error, ZeroDivisionError)

    def test_try_catch_specific_exception(self):
        def raise_value_error():
            raise ValueError("test")

        result = try_catch(raise_value_error, ValueError)
        assert result.is_err()
        assert isinstance(result.error, ValueError)


class TestCollectResults:
    """Tests for collect_results function."""

    def test_collect_all_ok(self):
        results = [Ok(1), Ok(2), Ok(3)]
        collected = collect_results(results)
        assert collected.is_ok()
        assert collected.unwrap() == [1, 2, 3]

    def test_collect_with_err(self):
        results = [Ok(1), Err("error"), Ok(3)]
        collected = collect_results(results)
        assert collected.is_err()
        assert collected.error == "error"

    def test_collect_empty_list(self):
        results = []
        collected = collect_results(results)
        assert collected.is_ok()
        assert collected.unwrap() == []

    def test_collect_first_err_returned(self):
        results = [Ok(1), Err("first"), Err("second")]
        collected = collect_results(results)
        assert collected.error == "first"


class TestResultFromDict:
    """Tests for result_from_dict function."""

    def test_from_dict_ok(self):
        d = {"type": "Ok", "value": 42}
        result = result_from_dict(d)
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_from_dict_err(self):
        d = {"type": "Err", "error": "error"}
        result = result_from_dict(d)
        assert result.is_err()
        assert result.error == "error"

    def test_from_dict_missing_type(self):
        d = {"value": 42}
        with pytest.raises(ValueError, match="Missing 'type'"):
            result_from_dict(d)

    def test_from_dict_invalid_type(self):
        d = {"type": "Invalid", "value": 42}
        with pytest.raises(ValueError, match="Invalid Result type"):
            result_from_dict(d)

    def test_from_dict_missing_value(self):
        d = {"type": "Ok"}
        with pytest.raises(ValueError, match="Missing 'value'"):
            result_from_dict(d)

    def test_from_dict_missing_error(self):
        d = {"type": "Err"}
        with pytest.raises(ValueError, match="Missing 'error'"):
            result_from_dict(d)


class TestResultRoundTrip:
    """Tests for Result serialization round-trip."""

    def test_ok_round_trip(self):
        original = Ok(42)
        d = original.to_dict()
        restored = result_from_dict(d)
        assert restored.unwrap() == original.unwrap()

    def test_err_round_trip(self):
        original = Err("error")
        d = original.to_dict()
        restored = result_from_dict(d)
        assert restored.error == original.error


from hypothesis import given, settings, strategies as st


class TestResultMonadLawsProperties:
    """Property-based tests for Result monad laws.

    **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
    **Validates: Requirements 4.3**
    """

    @given(value=st.integers())
    @settings(max_examples=100, deadline=5000)
    def test_left_identity(self, value: int) -> None:
        """Property: Left identity - return a >>= f ≡ f a.

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """

        def f(x):
            return Ok(x * 2)

        # return a >>= f
        left = Ok(value).bind(f)
        # f a
        right = f(value)

        assert left.unwrap() == right.unwrap()

    @given(value=st.integers())
    @settings(max_examples=100, deadline=5000)
    def test_right_identity(self, value: int) -> None:
        """Property: Right identity - m >>= return ≡ m.

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """
        m = Ok(value)

        # m >>= return
        result = m.bind(lambda x: Ok(x))

        assert result.unwrap() == m.unwrap()

    @given(value=st.integers())
    @settings(max_examples=100, deadline=5000)
    def test_associativity(self, value: int) -> None:
        """Property: Associativity - (m >>= f) >>= g ≡ m >>= (λx → f x >>= g).

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """

        def f(x):
            return Ok(x + 1)

        def g(x):
            return Ok(x * 2)

        m = Ok(value)

        # (m >>= f) >>= g
        left = m.bind(f).bind(g)
        # m >>= (λx → f x >>= g)
        right = m.bind(lambda x: f(x).bind(g))

        assert left.unwrap() == right.unwrap()

    @given(value=st.integers(), error=st.text(min_size=1, max_size=20))
    @settings(max_examples=100, deadline=5000)
    def test_err_propagation(self, value: int, error: str) -> None:
        """Property: Err propagates through bind operations.

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """
        err_result = Err(error)

        def f(x):
            return Ok(x * 2)

        result = err_result.bind(f)

        assert result.is_err()
        assert result.error == error

    @given(value=st.integers())
    @settings(max_examples=100, deadline=5000)
    def test_map_preserves_ok(self, value: int) -> None:
        """Property: map preserves Ok structure.

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """
        result = Ok(value).map(lambda x: x * 2)

        assert result.is_ok()
        assert result.unwrap() == value * 2

    @given(
        value=st.one_of(st.integers(), st.text(max_size=50)),
    )
    @settings(max_examples=100, deadline=5000)
    def test_round_trip_serialization(self, value) -> None:
        """Property: to_dict/from_dict round-trip preserves value.

        **Feature: test-coverage-80-percent-v3, Property 11: Result Type Monad Laws**
        **Validates: Requirements 4.3**
        """
        original = Ok(value)
        serialized = original.to_dict()
        restored = result_from_dict(serialized)

        assert restored.is_ok()
        assert restored.unwrap() == value
