from infrastructure.cache.serializers import JsonSerializer


class TestJsonSerializer:
    def test_serialize(self) -> None:
        serializer = JsonSerializer[dict[str, str]]()
        data = {"key": "value"}
        serialized = serializer.serialize(data)
        assert serialized == b'{"key": "value"}'

    def test_deserialize(self) -> None:
        serializer = JsonSerializer[dict[str, str]]()
        data = b'{"key": "value"}'
        deserialized = serializer.deserialize(data)
        assert deserialized == {"key": "value"}

    def test_round_trip(self) -> None:
        serializer = JsonSerializer[dict[str, str]]()
        data = {"key": "value", "another": "one"}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data
