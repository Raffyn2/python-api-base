"""Unit tests for HTTP client JSON types.

Tests JsonPrimitive, JsonValue, JsonObject, JsonArray type aliases.
"""

from infrastructure.httpclient.types import (
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
)


class TestJsonTypes:
    """Tests for JSON type aliases."""

    def test_json_primitive_string(self) -> None:
        """Test string is valid JsonPrimitive."""
        value: JsonPrimitive = "test"
        assert value == "test"

    def test_json_primitive_int(self) -> None:
        """Test int is valid JsonPrimitive."""
        value: JsonPrimitive = 42
        assert value == 42

    def test_json_primitive_float(self) -> None:
        """Test float is valid JsonPrimitive."""
        value: JsonPrimitive = 3.14
        assert value == 3.14

    def test_json_primitive_bool(self) -> None:
        """Test bool is valid JsonPrimitive."""
        value: JsonPrimitive = True
        assert value is True

    def test_json_primitive_none(self) -> None:
        """Test None is valid JsonPrimitive."""
        value: JsonPrimitive = None
        assert value is None

    def test_json_object(self) -> None:
        """Test dict is valid JsonObject."""
        value: JsonObject = {"key": "value", "number": 42}
        assert value["key"] == "value"
        assert value["number"] == 42

    def test_json_array(self) -> None:
        """Test list is valid JsonArray."""
        value: JsonArray = [1, 2, 3, "test"]
        assert len(value) == 4
        assert value[0] == 1
        assert value[3] == "test"

    def test_json_value_nested(self) -> None:
        """Test nested JSON structure."""
        value: JsonValue = {
            "name": "test",
            "items": [1, 2, 3],
            "nested": {
                "key": "value",
            },
        }
        assert isinstance(value, dict)
        assert value["name"] == "test"

    def test_exports(self) -> None:
        """Test all types are exported."""
        from infrastructure.httpclient import types
        
        assert hasattr(types, "JsonPrimitive")
        assert hasattr(types, "JsonValue")
        assert hasattr(types, "JsonObject")
        assert hasattr(types, "JsonArray")
