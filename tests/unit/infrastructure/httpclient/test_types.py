"""Unit tests for HTTP client types.

Tests JSON type definitions.
"""

from infrastructure.httpclient.types import (
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
)


class TestJsonTypes:
    """Tests for JSON type definitions."""

    def test_json_primitive_string(self) -> None:
        """Test string is valid JsonPrimitive."""
        value: JsonPrimitive = "hello"
        assert isinstance(value, str)

    def test_json_primitive_int(self) -> None:
        """Test int is valid JsonPrimitive."""
        value: JsonPrimitive = 42
        assert isinstance(value, int)

    def test_json_primitive_float(self) -> None:
        """Test float is valid JsonPrimitive."""
        value: JsonPrimitive = 3.14
        assert isinstance(value, float)

    def test_json_primitive_bool(self) -> None:
        """Test bool is valid JsonPrimitive."""
        value: JsonPrimitive = True
        assert isinstance(value, bool)

    def test_json_primitive_none(self) -> None:
        """Test None is valid JsonPrimitive."""
        value: JsonPrimitive = None
        assert value is None

    def test_json_object_empty(self) -> None:
        """Test empty dict is valid JsonObject."""
        obj: JsonObject = {}
        assert isinstance(obj, dict)

    def test_json_object_with_primitives(self) -> None:
        """Test dict with primitives is valid JsonObject."""
        obj: JsonObject = {
            "name": "test",
            "count": 42,
            "active": True,
            "value": None,
        }
        assert obj["name"] == "test"
        assert obj["count"] == 42

    def test_json_object_nested(self) -> None:
        """Test nested dict is valid JsonObject."""
        obj: JsonObject = {
            "user": {
                "name": "John",
                "age": 30,
            },
        }
        assert isinstance(obj["user"], dict)

    def test_json_array_empty(self) -> None:
        """Test empty list is valid JsonArray."""
        arr: JsonArray = []
        assert isinstance(arr, list)

    def test_json_array_with_primitives(self) -> None:
        """Test list with primitives is valid JsonArray."""
        arr: JsonArray = ["a", "b", "c"]
        assert len(arr) == 3

    def test_json_array_mixed(self) -> None:
        """Test list with mixed types is valid JsonArray."""
        arr: JsonArray = [1, "two", True, None]
        assert len(arr) == 4

    def test_json_value_complex(self) -> None:
        """Test complex nested structure."""
        value: JsonValue = {
            "users": [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 30},
            ],
            "total": 2,
            "active": True,
        }
        assert isinstance(value, dict)
