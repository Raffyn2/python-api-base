"""Unit tests for generics config module.

Tests BaseConfig and ConfigBuilder.
"""

from infrastructure.generics.core.config import BaseConfig, ConfigBuilder


class TestBaseConfig:
    """Tests for BaseConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BaseConfig()
        assert config.enabled is True
        assert config.debug is False
        assert config.timeout == 30.0
        assert config.retry_attempts == 3
        assert config.metadata == {}

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BaseConfig(
            enabled=False,
            debug=True,
            timeout=60.0,
            retry_attempts=5,
            metadata={"env": "test"},
        )
        assert config.enabled is False
        assert config.debug is True
        assert config.timeout == 60.0
        assert config.retry_attempts == 5
        assert config.metadata["env"] == "test"


class TestConfigBuilder:
    """Tests for ConfigBuilder."""

    def test_with_timeout(self) -> None:
        """Test setting timeout."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_timeout(60.0)
        values = builder.get_values()
        assert values["timeout"] == 60.0

    def test_with_retry(self) -> None:
        """Test setting retry attempts."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_retry(5)
        values = builder.get_values()
        assert values["retry_attempts"] == 5

    def test_with_debug(self) -> None:
        """Test enabling debug mode."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_debug(True)
        values = builder.get_values()
        assert values["debug"] is True

    def test_with_metadata(self) -> None:
        """Test adding metadata."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_metadata("key1", "value1")
        builder.with_metadata("key2", "value2")
        values = builder.get_values()
        assert values["metadata"]["key1"] == "value1"
        assert values["metadata"]["key2"] == "value2"

    def test_with_value(self) -> None:
        """Test setting arbitrary value."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_value("enabled", False)
        values = builder.get_values()
        assert values["enabled"] is False

    def test_chaining(self) -> None:
        """Test method chaining."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        result = builder.with_timeout(60.0).with_retry(5).with_debug(True)
        assert result is builder  # Returns self

    def test_build(self) -> None:
        """Test building configuration."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        config = builder.with_timeout(45.0).with_retry(2).build(BaseConfig)
        assert isinstance(config, BaseConfig)
        assert config.timeout == 45.0
        assert config.retry_attempts == 2

    def test_get_values_returns_copy(self) -> None:
        """Test get_values returns a copy."""
        builder: ConfigBuilder[BaseConfig] = ConfigBuilder()
        builder.with_timeout(30.0)
        values1 = builder.get_values()
        values2 = builder.get_values()
        assert values1 is not values2
        assert values1 == values2
