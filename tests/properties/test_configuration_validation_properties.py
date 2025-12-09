"""Property-based tests for configuration validation.

**Feature: test-coverage-90-percent, Property 7: Configuration Validation**
**Validates: Requirements 3.5**
"""

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings


class TestConfig(BaseSettings):
    """Test configuration for validation testing."""
    app_name: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    debug: bool = False
    api_key: str | None = None


class RequiredFieldsConfig(BaseSettings):
    """Configuration with required fields."""
    database_url: str
    secret_key: str
    api_version: str = "v1"


class TestConfigurationValidationProperties:
    """Property-based tests for configuration validation.
    
    **Feature: test-coverage-90-percent, Property 7: Configuration Validation**
    **Validates: Requirements 3.5**
    """

    @given(
        app_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        port=st.integers(min_value=1, max_value=65535),
        debug=st.booleans()
    )
    @settings(max_examples=100)
    def test_valid_config_always_loads(
        self, app_name: str, port: int, debug: bool
    ) -> None:
        """Valid configuration should always load successfully.
        
        *For any* valid configuration values, loading should succeed.
        """
        config = TestConfig(
            app_name=app_name,
            port=port,
            debug=debug
        )
        
        assert config.app_name == app_name
        assert config.port == port
        assert config.debug == debug

    @given(port=st.integers(min_value=1, max_value=65535))
    @settings(max_examples=50)
    def test_empty_app_name_fails(self, port: int) -> None:
        """Empty app_name should fail validation.
        
        *For any* configuration with empty app_name, loading should fail.
        """
        try:
            TestConfig(app_name="", port=port)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(
        app_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=50)
    def test_invalid_port_zero_fails(self, app_name: str) -> None:
        """Port 0 should fail validation.
        
        *For any* configuration with port=0, loading should fail.
        """
        try:
            TestConfig(app_name=app_name, port=0)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(
        app_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=50)
    def test_invalid_port_too_high_fails(self, app_name: str) -> None:
        """Port > 65535 should fail validation.
        
        *For any* configuration with port > 65535, loading should fail.
        """
        try:
            TestConfig(app_name=app_name, port=65536)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(
        app_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        port=st.integers(min_value=1, max_value=65535)
    )
    @settings(max_examples=50)
    def test_optional_field_can_be_none(self, app_name: str, port: int) -> None:
        """Optional fields should accept None.
        
        *For any* valid config, optional fields can be None.
        """
        config = TestConfig(
            app_name=app_name,
            port=port,
            api_key=None
        )
        
        assert config.api_key is None

    @given(
        app_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        port=st.integers(min_value=1, max_value=65535),
        api_key=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_optional_field_accepts_value(
        self, app_name: str, port: int, api_key: str
    ) -> None:
        """Optional fields should accept values.
        
        *For any* valid config with optional field set, it should be stored.
        """
        config = TestConfig(
            app_name=app_name,
            port=port,
            api_key=api_key
        )
        
        assert config.api_key == api_key

    @given(
        database_url=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        secret_key=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    @settings(max_examples=50)
    def test_required_fields_must_be_present(
        self, database_url: str, secret_key: str
    ) -> None:
        """Required fields must be present.
        
        *For any* valid required field values, config should load.
        """
        config = RequiredFieldsConfig(
            database_url=database_url,
            secret_key=secret_key
        )
        
        assert config.database_url == database_url
        assert config.secret_key == secret_key

    @given(secret_key=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=30)
    def test_missing_required_field_fails(self, secret_key: str) -> None:
        """Missing required field should fail validation.
        
        *For any* configuration missing required field, loading should fail
        with clear error message.
        """
        try:
            # Missing database_url
            RequiredFieldsConfig(secret_key=secret_key)  # type: ignore
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            # Error should mention the missing field
            error_str = str(e)
            assert "database_url" in error_str.lower() or "field required" in error_str.lower()

    @given(
        database_url=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        secret_key=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        api_version=st.text(min_size=1, max_size=20).filter(lambda x: x.strip())
    )
    @settings(max_examples=50)
    def test_default_values_can_be_overridden(
        self, database_url: str, secret_key: str, api_version: str
    ) -> None:
        """Default values should be overridable.
        
        *For any* valid config, default values can be overridden.
        """
        config = RequiredFieldsConfig(
            database_url=database_url,
            secret_key=secret_key,
            api_version=api_version
        )
        
        assert config.api_version == api_version

    @given(
        database_url=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        secret_key=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    @settings(max_examples=50)
    def test_default_values_used_when_not_provided(
        self, database_url: str, secret_key: str
    ) -> None:
        """Default values should be used when not provided.
        
        *For any* valid config without optional field, default should be used.
        """
        config = RequiredFieldsConfig(
            database_url=database_url,
            secret_key=secret_key
        )
        
        assert config.api_version == "v1"  # Default value
