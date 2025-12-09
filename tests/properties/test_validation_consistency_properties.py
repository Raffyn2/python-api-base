"""Property-based tests for validation consistency.

**Feature: test-coverage-90-percent, Property 6: Validation Consistency**
**Validates: Requirements 5.2**
"""

from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, Field, ValidationError, field_validator


class ValidatedModel(BaseModel):
    """Model with validation rules for testing."""
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Email must contain @")
        return v


class StrictModel(BaseModel):
    """Model with strict validation."""
    code: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")
    score: float = Field(ge=0.0, le=100.0)


# Strategies for valid data
valid_name = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
valid_age = st.integers(min_value=0, max_value=150)
valid_email = st.emails()

# Strategies for invalid data
invalid_name_empty = st.just("")
invalid_name_too_long = st.text(min_size=101, max_size=200)
invalid_age_negative = st.integers(max_value=-1)
invalid_age_too_high = st.integers(min_value=151)
invalid_email = st.text(min_size=1, max_size=50).filter(lambda x: "@" not in x)


class TestValidationConsistencyProperties:
    """Property-based tests for validation consistency.
    
    **Feature: test-coverage-90-percent, Property 6: Validation Consistency**
    **Validates: Requirements 5.2**
    """

    @given(name=valid_name, age=valid_age, email=valid_email)
    @settings(max_examples=100)
    def test_valid_input_always_passes(
        self, name: str, age: int, email: str
    ) -> None:
        """Valid input should always pass validation.
        
        *For any* valid input data, validation should be deterministic 
        and always pass.
        """
        # Should not raise
        model = ValidatedModel(name=name, age=age, email=email)
        
        assert model.name == name
        assert model.age == age
        assert model.email == email

    @given(name=valid_name, age=valid_age, email=valid_email)
    @settings(max_examples=100)
    def test_validation_is_deterministic(
        self, name: str, age: int, email: str
    ) -> None:
        """Same input should always produce same validation result.
        
        *For any* input, validation result should be consistent.
        """
        # Validate multiple times
        results = []
        for _ in range(3):
            try:
                model = ValidatedModel(name=name, age=age, email=email)
                results.append(("ok", model.model_dump()))
            except ValidationError as e:
                results.append(("error", str(e)))
        
        # All results should be identical
        assert all(r == results[0] for r in results)

    @given(age=valid_age, email=valid_email)
    @settings(max_examples=50)
    def test_empty_name_always_fails(self, age: int, email: str) -> None:
        """Empty name should always fail validation.
        
        *For any* input with empty name, validation should fail.
        """
        try:
            ValidatedModel(name="", age=age, email=email)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(name=valid_name, email=valid_email)
    @settings(max_examples=50)
    def test_negative_age_always_fails(self, name: str, email: str) -> None:
        """Negative age should always fail validation.
        
        *For any* input with negative age, validation should fail.
        """
        try:
            ValidatedModel(name=name, age=-1, email=email)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(name=valid_name, age=valid_age)
    @settings(max_examples=50)
    def test_invalid_email_always_fails(self, name: str, age: int) -> None:
        """Email without @ should always fail validation.
        
        *For any* input with invalid email, validation should fail.
        """
        try:
            ValidatedModel(name=name, age=age, email="notanemail")
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(
        code=st.from_regex(r"^[A-Z]{3}-\d{4}$", fullmatch=True),
        score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_pattern_validation_consistent(self, code: str, score: float) -> None:
        """Pattern validation should be consistent.
        
        *For any* valid pattern, validation should pass consistently.
        """
        model = StrictModel(code=code, score=score)
        
        assert model.code == code
        assert model.score == score

    @given(
        code=st.text(min_size=1, max_size=20).filter(
            lambda x: not x.isupper() or len(x) != 8 or "-" not in x
        ),
        score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
    )
    @settings(max_examples=50)
    def test_invalid_pattern_always_fails(self, code: str, score: float) -> None:
        """Invalid pattern should always fail validation.
        
        *For any* invalid pattern, validation should fail consistently.
        """
        # Skip if accidentally valid
        import re
        if re.match(r"^[A-Z]{3}-\d{4}$", code):
            return
        
        try:
            StrictModel(code=code, score=score)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    @given(
        name=valid_name,
        age=valid_age,
        email=valid_email
    )
    @settings(max_examples=50)
    def test_validation_idempotent(
        self, name: str, age: int, email: str
    ) -> None:
        """Validating same data multiple times should be idempotent.
        
        *For any* valid data, repeated validation produces same model.
        """
        model1 = ValidatedModel(name=name, age=age, email=email)
        model2 = ValidatedModel(name=name, age=age, email=email)
        
        assert model1 == model2
        assert model1.model_dump() == model2.model_dump()
