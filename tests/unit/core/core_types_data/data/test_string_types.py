"""Tests for string types module.

Tests Pydantic annotated types for string validation.
"""

import pytest
from pydantic import BaseModel, ValidationError

# Import using full path to avoid conflict with Python's built-in types module
from core.types.data.string_types import (
    Email,
    HttpUrl,
    ISODateStr,
    LongStr,
    MediumStr,
    NonEmptyStr,
    PhoneNumber,
    ShortStr,
    Slug,
    TrimmedStr,
    VersionStr,
)


class NonEmptyStrModel(BaseModel):
    """Model for testing NonEmptyStr."""

    value: NonEmptyStr


class TrimmedStrModel(BaseModel):
    """Model for testing TrimmedStr."""

    value: TrimmedStr


class ShortStrModel(BaseModel):
    """Model for testing ShortStr."""

    value: ShortStr


class MediumStrModel(BaseModel):
    """Model for testing MediumStr."""

    value: MediumStr


class LongStrModel(BaseModel):
    """Model for testing LongStr."""

    value: LongStr


class SlugModel(BaseModel):
    """Model for testing Slug."""

    value: Slug


class EmailModel(BaseModel):
    """Model for testing Email."""

    value: Email


class PhoneNumberModel(BaseModel):
    """Model for testing PhoneNumber."""

    value: PhoneNumber


class HttpUrlModel(BaseModel):
    """Model for testing HttpUrl."""

    value: HttpUrl


class VersionStrModel(BaseModel):
    """Model for testing VersionStr."""

    value: VersionStr


class ISODateStrModel(BaseModel):
    """Model for testing ISODateStr."""

    value: ISODateStr


class TestNonEmptyStr:
    """Tests for NonEmptyStr type."""

    def test_valid_string(self) -> None:
        model = NonEmptyStrModel(value="hello")
        assert model.value == "hello"

    def test_strips_whitespace(self) -> None:
        model = NonEmptyStrModel(value="  hello  ")
        assert model.value == "hello"

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValidationError):
            NonEmptyStrModel(value="")

    def test_invalid_whitespace_only(self) -> None:
        with pytest.raises(ValidationError):
            NonEmptyStrModel(value="   ")


class TestTrimmedStr:
    """Tests for TrimmedStr type."""

    def test_valid_string(self) -> None:
        model = TrimmedStrModel(value="hello")
        assert model.value == "hello"

    def test_strips_whitespace(self) -> None:
        model = TrimmedStrModel(value="  hello world  ")
        assert model.value == "hello world"

    def test_allows_empty(self) -> None:
        model = TrimmedStrModel(value="")
        assert model.value == ""


class TestShortStr:
    """Tests for ShortStr type."""

    def test_valid_string(self) -> None:
        model = ShortStrModel(value="short")
        assert model.value == "short"

    def test_max_length(self) -> None:
        model = ShortStrModel(value="a" * 100)
        assert len(model.value) == 100

    def test_invalid_too_long(self) -> None:
        with pytest.raises(ValidationError):
            ShortStrModel(value="a" * 101)

    def test_strips_whitespace(self) -> None:
        model = ShortStrModel(value="  test  ")
        assert model.value == "test"


class TestMediumStr:
    """Tests for MediumStr type."""

    def test_valid_string(self) -> None:
        model = MediumStrModel(value="medium length string")
        assert model.value == "medium length string"

    def test_max_length(self) -> None:
        model = MediumStrModel(value="a" * 500)
        assert len(model.value) == 500

    def test_invalid_too_long(self) -> None:
        with pytest.raises(ValidationError):
            MediumStrModel(value="a" * 501)


class TestLongStr:
    """Tests for LongStr type."""

    def test_valid_string(self) -> None:
        model = LongStrModel(value="a long string " * 100)
        assert "long string" in model.value

    def test_max_length(self) -> None:
        model = LongStrModel(value="a" * 5000)
        assert len(model.value) == 5000

    def test_invalid_too_long(self) -> None:
        with pytest.raises(ValidationError):
            LongStrModel(value="a" * 5001)


class TestSlug:
    """Tests for Slug type."""

    def test_valid_simple(self) -> None:
        model = SlugModel(value="hello")
        assert model.value == "hello"

    def test_valid_with_hyphens(self) -> None:
        model = SlugModel(value="hello-world")
        assert model.value == "hello-world"

    def test_valid_with_numbers(self) -> None:
        model = SlugModel(value="post-123")
        assert model.value == "post-123"

    def test_invalid_uppercase(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="Hello")

    def test_invalid_spaces(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="hello world")

    def test_invalid_special_chars(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="hello_world")

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="")

    def test_invalid_starts_with_hyphen(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="-hello")

    def test_invalid_ends_with_hyphen(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="hello-")


class TestEmail:
    """Tests for Email type."""

    def test_valid_simple(self) -> None:
        model = EmailModel(value="user@example.com")
        assert model.value == "user@example.com"

    def test_valid_with_subdomain(self) -> None:
        model = EmailModel(value="user@mail.example.com")
        assert model.value == "user@mail.example.com"

    def test_valid_with_plus(self) -> None:
        model = EmailModel(value="user+tag@example.com")
        assert model.value == "user+tag@example.com"

    def test_invalid_no_at(self) -> None:
        with pytest.raises(ValidationError):
            EmailModel(value="userexample.com")

    def test_invalid_no_domain(self) -> None:
        with pytest.raises(ValidationError):
            EmailModel(value="user@")

    def test_invalid_no_tld(self) -> None:
        with pytest.raises(ValidationError):
            EmailModel(value="user@example")


class TestPhoneNumber:
    """Tests for PhoneNumber type."""

    def test_valid_simple(self) -> None:
        model = PhoneNumberModel(value="1234567890")
        assert model.value == "1234567890"

    def test_valid_with_country_code(self) -> None:
        model = PhoneNumberModel(value="+1 234 567 8900")
        assert model.value == "+1 234 567 8900"

    def test_valid_with_dashes(self) -> None:
        model = PhoneNumberModel(value="123-456-7890")
        assert model.value == "123-456-7890"

    def test_valid_with_parentheses(self) -> None:
        model = PhoneNumberModel(value="(123) 456-7890")
        assert model.value == "(123) 456-7890"

    def test_invalid_too_short(self) -> None:
        with pytest.raises(ValidationError):
            PhoneNumberModel(value="12345")

    def test_invalid_letters(self) -> None:
        with pytest.raises(ValidationError):
            PhoneNumberModel(value="123-ABC-7890")


class TestHttpUrl:
    """Tests for HttpUrl type."""

    def test_valid_http(self) -> None:
        model = HttpUrlModel(value="http://example.com")
        assert model.value == "http://example.com"

    def test_valid_https(self) -> None:
        model = HttpUrlModel(value="https://example.com")
        assert model.value == "https://example.com"

    def test_valid_with_path(self) -> None:
        model = HttpUrlModel(value="https://example.com/path/to/page")
        assert model.value == "https://example.com/path/to/page"

    def test_valid_with_query(self) -> None:
        model = HttpUrlModel(value="https://example.com?q=test")
        assert model.value == "https://example.com?q=test"

    def test_invalid_no_protocol(self) -> None:
        with pytest.raises(ValidationError):
            HttpUrlModel(value="example.com")

    def test_invalid_ftp(self) -> None:
        with pytest.raises(ValidationError):
            HttpUrlModel(value="ftp://example.com")


class TestVersionStr:
    """Tests for VersionStr type."""

    def test_valid_simple(self) -> None:
        model = VersionStrModel(value="1.0.0")
        assert model.value == "1.0.0"

    def test_valid_with_v_prefix(self) -> None:
        model = VersionStrModel(value="v1.0.0")
        assert model.value == "v1.0.0"

    def test_valid_with_prerelease(self) -> None:
        model = VersionStrModel(value="1.0.0-beta")
        assert model.value == "1.0.0-beta"

    def test_valid_two_parts(self) -> None:
        model = VersionStrModel(value="1.0")
        assert model.value == "1.0"

    def test_valid_single_number(self) -> None:
        model = VersionStrModel(value="1")
        assert model.value == "1"

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValidationError):
            VersionStrModel(value="")

    def test_invalid_letters_only(self) -> None:
        with pytest.raises(ValidationError):
            VersionStrModel(value="abc")


class TestISODateStr:
    """Tests for ISODateStr type."""

    def test_valid_date_only(self) -> None:
        model = ISODateStrModel(value="2024-01-15")
        assert model.value == "2024-01-15"

    def test_valid_datetime(self) -> None:
        model = ISODateStrModel(value="2024-01-15T10:30:00")
        assert model.value == "2024-01-15T10:30:00"

    def test_valid_datetime_with_z(self) -> None:
        model = ISODateStrModel(value="2024-01-15T10:30:00Z")
        assert model.value == "2024-01-15T10:30:00Z"

    def test_valid_datetime_with_offset(self) -> None:
        model = ISODateStrModel(value="2024-01-15T10:30:00+05:30")
        assert model.value == "2024-01-15T10:30:00+05:30"

    def test_valid_datetime_with_milliseconds(self) -> None:
        model = ISODateStrModel(value="2024-01-15T10:30:00.123Z")
        assert model.value == "2024-01-15T10:30:00.123Z"

    def test_invalid_format(self) -> None:
        with pytest.raises(ValidationError):
            ISODateStrModel(value="01/15/2024")

    def test_invalid_empty(self) -> None:
        with pytest.raises(ValidationError):
            ISODateStrModel(value="")
