"""Unit tests for core/base/patterns/result.py.

Tests Result pattern for explicit error handling.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

import pytest

from core.base.patterns.result import (
    Err,
    Ok,
    Result,
    collect_results,
    err,
    ok,
    result_from_dict,
    try_catch,
)


class TestOk:
    """Tests for Ok class."""

    def test_create_ok(self) -> None:
        """Ok should store value."""
        result = Ok(42)
        
        assert result.value == 42

    def test_is_ok_returns_true(self) -> None:
        """is_ok should return True for Ok."""
        result = Ok("success")
        
        assert result.is_ok() is True

    def test_is_err_returns_false(self) -> None:
        """is_err should return False for Ok."""
        result = Ok("success")
        
        assert result.is_err() is False

    def test_unwrap_returns_value(self) -> None:
        """unwrap should return the value."""
        result = Ok(100)
        
        assert result.unwrap() == 100

    def test_unwrap_or_returns_value(self) -> None:
        """unwrap_or should return the value, not default."""
        result = Ok(100)
        
        assert result.unwrap_or(0) == 100

    def test_unwrap_or_else_returns_value(self) -> None:
        """unwrap_or_else should return the value, not computed default."""
        result = Ok(100)
        
        assert result.unwrap_or_else(lambda: 0) == 100

    def test_expect_returns_value(self) -> None:
        """expect should return the value."""
        result = Ok(100)
        
        assert result.expect("should not fail") == 100

    def test_map_transforms_value(self) -> None:
        """map should transform the value."""
        result = Ok(10)
        
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.value == 20

    def test_bind_chains_operations(self) -> None:
        """bind should chain Result-returning operations."""
        result = Ok(10)
        
        chained = result.bind(lambda x: Ok(x + 5))
        
        assert chained.value == 15

    def test_and_then_alias_for_bind(self) -> None:
        """and_then should work like bind."""
        result = Ok(10)
        
        chained = result.and_then(lambda x: Ok(x * 3))
        
        assert chained.value == 30

    def test_or_else_returns_self(self) -> None:
        """or_else should return self for Ok."""
        result = Ok(10)
        
        recovered = result.or_else(lambda _: Ok(0))
        
        assert recovered.value == 10

    def test_map_err_no_op(self) -> None:
        """map_err should be no-op for Ok."""
        result = Ok(10)
        
        mapped = result.map_err(lambda e: f"Error: {e}")
        
        assert mapped.value == 10

    def test_match_calls_on_ok(self) -> None:
        """match should call on_ok function."""
        result = Ok(10)
        
        matched = result.match(
            on_ok=lambda x: f"Success: {x}",
            on_err=lambda e: f"Error: {e}"
        )
        
        assert matched == "Success: 10"

    def test_inspect_calls_function(self) -> None:
        """inspect should call function with value."""
        result = Ok(10)
        captured = []
        
        result.inspect(lambda x: captured.append(x))
        
        assert captured == [10]

    def test_inspect_err_no_op(self) -> None:
        """inspect_err should be no-op for Ok."""
        result = Ok(10)
        captured = []
        
        result.inspect_err(lambda e: captured.append(e))
        
        assert captured == []

    def test_to_dict_serialization(self) -> None:
        """to_dict should serialize Ok."""
        result = Ok("test")
        
        data = result.to_dict()
        
        assert data == {"type": "Ok", "value": "test"}


class TestErr:
    """Tests for Err class."""

    def test_create_err(self) -> None:
        """Err should store error."""
        result = Err("something went wrong")
        
        assert result.error == "something went wrong"

    def test_is_ok_returns_false(self) -> None:
        """is_ok should return False for Err."""
        result = Err("error")
        
        assert result.is_ok() is False

    def test_is_err_returns_true(self) -> None:
        """is_err should return True for Err."""
        result = Err("error")
        
        assert result.is_err() is True

    def test_unwrap_raises(self) -> None:
        """unwrap should raise for Err."""
        result = Err("error message")
        
        with pytest.raises(ValueError, match="Called unwrap on Err"):
            result.unwrap()

    def test_unwrap_or_returns_default(self) -> None:
        """unwrap_or should return default for Err."""
        result = Err("error")
        
        assert result.unwrap_or(42) == 42

    def test_unwrap_or_else_computes_default(self) -> None:
        """unwrap_or_else should compute default from error."""
        result = Err("error")
        
        assert result.unwrap_or_else(lambda e: len(e)) == 5

    def test_expect_raises_with_message(self) -> None:
        """expect should raise with custom message."""
        result = Err("error")
        
        with pytest.raises(ValueError, match="Custom message"):
            result.expect("Custom message")

    def test_map_no_op(self) -> None:
        """map should be no-op for Err."""
        result = Err("error")
        
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.error == "error"

    def test_bind_no_op(self) -> None:
        """bind should be no-op for Err."""
        result = Err("error")
        
        chained = result.bind(lambda x: Ok(x + 5))
        
        assert chained.error == "error"

    def test_and_then_no_op(self) -> None:
        """and_then should be no-op for Err."""
        result = Err("error")
        
        chained = result.and_then(lambda x: Ok(x * 3))
        
        assert chained.error == "error"

    def test_or_else_handles_error(self) -> None:
        """or_else should handle error."""
        result: Result[int, str] = Err("error")
        
        recovered = result.or_else(lambda e: Ok(len(e)))
        
        assert recovered.value == 5

    def test_map_err_transforms_error(self) -> None:
        """map_err should transform error."""
        result = Err("error")
        
        mapped = result.map_err(lambda e: f"Wrapped: {e}")
        
        assert mapped.error == "Wrapped: error"

    def test_match_calls_on_err(self) -> None:
        """match should call on_err function."""
        result = Err("error")
        
        matched = result.match(
            on_ok=lambda x: f"Success: {x}",
            on_err=lambda e: f"Error: {e}"
        )
        
        assert matched == "Error: error"

    def test_inspect_no_op(self) -> None:
        """inspect should be no-op for Err."""
        result = Err("error")
        captured = []
        
        result.inspect(lambda x: captured.append(x))
        
        assert captured == []

    def test_inspect_err_calls_function(self) -> None:
        """inspect_err should call function with error."""
        result = Err("error")
        captured = []
        
        result.inspect_err(lambda e: captured.append(e))
        
        assert captured == ["error"]

    def test_to_dict_serialization(self) -> None:
        """to_dict should serialize Err."""
        result = Err("test error")
        
        data = result.to_dict()
        
        assert data == {"type": "Err", "error": "test error"}

    def test_flatten_no_op(self) -> None:
        """flatten should be no-op for Err."""
        result = Err("error")
        
        flattened = result.flatten()
        
        assert flattened.error == "error"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_ok_function(self) -> None:
        """ok() should create Ok result."""
        result = ok(42)
        
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_err_function(self) -> None:
        """err() should create Err result."""
        result = err("error")
        
        assert isinstance(result, Err)
        assert result.error == "error"

    def test_try_catch_success(self) -> None:
        """try_catch should return Ok on success."""
        result = try_catch(lambda: 42)
        
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_try_catch_failure(self) -> None:
        """try_catch should return Err on exception."""
        def failing_fn() -> int:
            raise ValueError("test error")
        
        result = try_catch(failing_fn, ValueError)
        
        assert result.is_err()

    def test_collect_results_all_ok(self) -> None:
        """collect_results should return Ok with all values."""
        results: list[Result[int, str]] = [Ok(1), Ok(2), Ok(3)]
        
        collected = collect_results(results)
        
        assert collected.is_ok()
        assert collected.unwrap() == [1, 2, 3]

    def test_collect_results_with_err(self) -> None:
        """collect_results should return first Err."""
        results: list[Result[int, str]] = [Ok(1), Err("error"), Ok(3)]
        
        collected = collect_results(results)
        
        assert collected.is_err()

    def test_collect_results_empty(self) -> None:
        """collect_results should return Ok with empty list."""
        results: list[Result[int, str]] = []
        
        collected = collect_results(results)
        
        assert collected.is_ok()
        assert collected.unwrap() == []


class TestResultFromDict:
    """Tests for result_from_dict function."""

    def test_deserialize_ok(self) -> None:
        """result_from_dict should deserialize Ok."""
        data = {"type": "Ok", "value": 42}
        
        result = result_from_dict(data)
        
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_deserialize_err(self) -> None:
        """result_from_dict should deserialize Err."""
        data = {"type": "Err", "error": "test error"}
        
        result = result_from_dict(data)
        
        assert result.is_err()

    def test_missing_type_raises(self) -> None:
        """result_from_dict should raise for missing type."""
        with pytest.raises(ValueError, match="Missing 'type' key"):
            result_from_dict({"value": 42})

    def test_invalid_type_raises(self) -> None:
        """result_from_dict should raise for invalid type."""
        with pytest.raises(ValueError, match="Invalid Result type"):
            result_from_dict({"type": "Invalid", "value": 42})

    def test_missing_value_raises(self) -> None:
        """result_from_dict should raise for missing value in Ok."""
        with pytest.raises(ValueError, match="Missing 'value' key"):
            result_from_dict({"type": "Ok"})

    def test_missing_error_raises(self) -> None:
        """result_from_dict should raise for missing error in Err."""
        with pytest.raises(ValueError, match="Missing 'error' key"):
            result_from_dict({"type": "Err"})

    def test_roundtrip_ok(self) -> None:
        """Ok should roundtrip through serialization."""
        original = Ok("test value")
        
        serialized = original.to_dict()
        deserialized = result_from_dict(serialized)
        
        assert deserialized.is_ok()
        assert deserialized.unwrap() == "test value"

    def test_roundtrip_err(self) -> None:
        """Err should roundtrip through serialization."""
        original = Err("test error")
        
        serialized = original.to_dict()
        deserialized = result_from_dict(serialized)
        
        assert deserialized.is_err()
