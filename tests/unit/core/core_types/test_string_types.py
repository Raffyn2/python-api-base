"""Tests for string type definitions.

Tests Email, Slug, NonEmptyStr, HttpUrl, etc.
"""

import pytest
from pydantic import BaseModel, ValidationError

from core.types import (
    Email,
    HttpUrl,
    ISODateStr,
    LongStr,
    MediumStr,
    NonEmptyStr,
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

    def test_empty_string_invalid(self) -> None:
        with pytest.raises(ValidationError):
            NonEmptyStrModel(value="")

    def test_whitespace_only_invalid(self) -> None:
        with pytest.raises(ValidationError):
            NonEmptyStrModel(value="   ")


class TestTrimmedStr:
    """Tests for TrimmedStr type."""

    def test_strips_whitespace(self) -> None:
        model = TrimmedStrModel(value="  hello  ")
        assert model.value == "hello"

    def test_empty_string_valid(self) -> None:
        model = TrimmedStrModel(value="")
        assert model.value == ""


class TestShortStr:
    """Tests for ShortStr type."""

    def test_valid_short_string(self) -> None:
        model = ShortStrModel(value="hello")
        assert model.value == "hello"

    def test_max_length(self) -> None:
        model = ShortStrModel(value="a" * 100)
        assert len(model.value) == 100

    def test_over_max_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ShortStrModel(value="a" * 101)


class TestMediumStr:
    """Tests for MediumStr type."""

    def test_valid_medium_string(self) -> None:
        model = MediumStrModel(value="hello world")
        assert model.value == "hello world"

    def test_max_length(self) -> None:
        model = MediumStrModel(value="a" * 500)
        assert len(model.value) == 500

    def test_over_max_invalid(self) -> None:
        with pytest.raises(ValidationError):
            MediumStrModel(value="a" * 501)


class TestLongStr:
    """Tests for LongStr type."""

    def test_valid_long_string(self) -> None:
        model = LongStrModel(value="a" * 1000)
        assert len(model.value) == 1000

    def test_max_length(self) -> None:
        model = LongStrModel(value="a" * 5000)
        assert len(model.value) == 5000

    def test_over_max_invalid(self) -> None:
        with pytest.raises(ValidationError):
            LongStrModel(value="a" * 5001)


class TestSlug:
    """Tests for Slug type."""

    def test_valid_simple_slug(self) -> None:
        model = SlugModel(value="hello")
        assert model.value == "hello"

    def test_valid_slug_with_hyphens(self) -> None:
        model = SlugModel(value="hello-world")
        assert model.value == "hello-world"

    def test_valid_slug_with_numbers(self) -> None:
        model = SlugModel(value="post-123")
        assert model.value == "post-123"

    def test_uppercase_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="Hello")

    def test_spaces_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="hello world")

    def test_underscores_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="hello_world")

    def test_empty_invalid(self) -> None:
        with pytest.raises(ValidationError):
            SlugModel(value="")


class TestEmail:
    """Tests for Email type."""

    def test_valid_email(self) -> None:
        model = EmailModel(value="user@example.com")
        assert model.value == "user@example.com"

    def test_valid_email_with_subdomain(self) -> None:
        model = EmailModel(value="user@mail.example.com")
        assert model.value == "user@mail.example.com"

    def test_valid_email_with_plus(self) -> None:
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


class TestHttpUrl:
    """Tests for HttpUrl type."""

    def test_valid_http(self) -> None:
        model = HttpUrlModel(value="http://example.com")
        assert model.value == "http://example.com"

    def test_valid_https(self) -> None:
        model = HttpUrlModel(value="https://example.com")
        assert model.value == "https://example.com"

    def test_valid_with_path(self) -> None:
        model = HttpUrlModel(value="https://example.com/path/to/resource")
        assert model.value == "https://example.com/path/to/resource"

    def test_valid_with_query(self) -> None:
        model = HttpUrlModel(value="https://example.com?query=value")
        assert model.value == "https://example.com?query=value"

    def test_invalid_no_protocol(self) -> None:
        with pytest.raises(ValidationError):
            HttpUrlModel(value="example.com")

    def test_invalid_ftp(self) -> None:
        with pytest.raises(ValidationError):
            HttpUrlModel(value="ftp://example.com")


class TestVersionStr:
    """Tests for VersionStr type."""

    def test_valid_simple_version(self) -> None:
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


class TestISODateStr:
    """Tests for ISODateStr type."""

    def test_valid_date(self) -> None:
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
            ISODateStrModel(value="15/01/2024")
