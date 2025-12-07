"""Unit tests for PII redaction processor.

Tests RedactionProcessor, PIIPattern, and redaction functions.
"""

import re

import pytest

from core.shared.logging.redaction import (
    PIIPattern,
    RedactionProcessor,
    create_redaction_processor,
)


class TestPIIPattern:
    """Tests for PIIPattern dataclass."""

    def test_redact_with_replacement(self) -> None:
        pattern = PIIPattern(
            name="test",
            pattern=re.compile(r"secret"),
            replacement="***",
        )
        result = pattern.redact("my secret value")
        assert result == "my *** value"

    def test_redact_with_mask_func(self) -> None:
        def mask(match: re.Match[str]) -> str:
            return f"[{len(match.group(0))} chars]"

        pattern = PIIPattern(
            name="test",
            pattern=re.compile(r"\w+"),
            mask_func=mask,
        )
        result = pattern.redact("hello")
        assert result == "[5 chars]"

    def test_redact_no_match(self) -> None:
        pattern = PIIPattern(
            name="test",
            pattern=re.compile(r"secret"),
            replacement="***",
        )
        result = pattern.redact("no match here")
        assert result == "no match here"


class TestRedactionProcessor:
    """Tests for RedactionProcessor."""

    @pytest.fixture
    def processor(self) -> RedactionProcessor:
        return RedactionProcessor()

    def test_redact_email(self, processor: RedactionProcessor) -> None:
        event = {"event": "User admin@example.com logged in"}
        result = processor(None, None, event)
        assert "admin@example.com" not in result["event"]
        assert "@example.com" in result["event"]

    def test_redact_password_json(self, processor: RedactionProcessor) -> None:
        event = {"event": '{"password": "secret123"}'}
        result = processor(None, None, event)
        assert "secret123" not in result["event"]
        assert '***"' in result["event"]

    def test_redact_password_field(self, processor: RedactionProcessor) -> None:
        event = {"event": "password=mysecret123"}
        result = processor(None, None, event)
        assert "mysecret123" not in result["event"]
        assert "password=***" in result["event"]

    def test_redact_credit_card(self, processor: RedactionProcessor) -> None:
        event = {"event": "Card: 4111-1111-1111-1111"}
        result = processor(None, None, event)
        assert "4111-1111-1111-1111" not in result["event"]
        assert "****-****-****-1111" in result["event"]

    def test_redact_ssn(self, processor: RedactionProcessor) -> None:
        event = {"event": "SSN: 123-45-6789"}
        result = processor(None, None, event)
        assert "123-45-6789" not in result["event"]
        assert "***-**-****" in result["event"]

    def test_redact_phone(self, processor: RedactionProcessor) -> None:
        event = {"event": "Phone: 555-123-4567"}
        result = processor(None, None, event)
        assert "555-123-4567" not in result["event"]
        assert "4567" in result["event"]

    def test_redact_bearer_token(self, processor: RedactionProcessor) -> None:
        event = {"event": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"}
        result = processor(None, None, event)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result["event"]
        assert "Bearer ***" in result["event"]

    def test_redact_api_key(self, processor: RedactionProcessor) -> None:
        event = {"event": "api_key=abcdef1234567890abcdef"}
        result = processor(None, None, event)
        assert "abcdef1234567890abcdef" not in result["event"]

    def test_redact_sensitive_field_names(self, processor: RedactionProcessor) -> None:
        event = {
            "event": "Login",
            "password": "secret123",
            "token": "abc123",
            "api_key": "key123",
        }
        result = processor(None, None, event)
        assert result["password"] == "***"
        assert result["token"] == "***"
        assert result["api_key"] == "***"

    def test_preserve_safe_fields(self, processor: RedactionProcessor) -> None:
        event = {
            "timestamp": "2024-01-01T00:00:00Z",
            "level": "info",
            "correlation_id": "abc-123",
            "service_name": "test-service",
        }
        result = processor(None, None, event)
        assert result["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["level"] == "info"
        assert result["correlation_id"] == "abc-123"

    def test_redact_nested_dict(self, processor: RedactionProcessor) -> None:
        event = {
            "event": "Request",
            "user": {
                "email": "test@example.com",
                "password": "secret",
            },
        }
        result = processor(None, None, event)
        assert "test@example.com" not in str(result)
        assert result["user"]["password"] == "***"

    def test_redact_list(self, processor: RedactionProcessor) -> None:
        event = {
            "event": "Emails",
            "emails": ["user1@example.com", "user2@example.com"],
        }
        result = processor(None, None, event)
        assert "user1@example.com" not in str(result)
        assert "user2@example.com" not in str(result)

    def test_disabled_processor(self) -> None:
        processor = RedactionProcessor(enabled=False)
        event = {"event": "Email: admin@example.com"}
        result = processor(None, None, event)
        assert result["event"] == "Email: admin@example.com"

    def test_add_pattern(self, processor: RedactionProcessor) -> None:
        processor.add_pattern(
            "custom",
            PIIPattern(
                name="custom",
                pattern=re.compile(r"CUST-\d{6}"),
                replacement="CUST-******",
            ),
        )
        event = {"event": "Customer: CUST-123456"}
        result = processor(None, None, event)
        assert "CUST-123456" not in result["event"]
        assert "CUST-******" in result["event"]

    def test_remove_pattern(self, processor: RedactionProcessor) -> None:
        processor.remove_pattern("email")
        event = {"event": "Email: admin@example.com"}
        result = processor(None, None, event)
        assert "admin@example.com" in result["event"]

    def test_non_string_values(self, processor: RedactionProcessor) -> None:
        event = {
            "event": "Test",
            "count": 42,
            "active": True,
            "data": None,
        }
        result = processor(None, None, event)
        assert result["count"] == 42
        assert result["active"] is True
        assert result["data"] is None


class TestCreateRedactionProcessor:
    """Tests for create_redaction_processor factory."""

    def test_default_processor(self) -> None:
        processor = create_redaction_processor()
        assert processor.enabled is True
        assert len(processor.patterns) > 0

    def test_disabled_processor(self) -> None:
        processor = create_redaction_processor(enabled=False)
        assert processor.enabled is False

    def test_extra_patterns(self) -> None:
        extra = {
            "custom": PIIPattern(
                name="custom",
                pattern=re.compile(r"CUSTOM"),
                replacement="***",
            )
        }
        processor = create_redaction_processor(extra_patterns=extra)
        assert "custom" in processor.patterns

    def test_extra_fields(self) -> None:
        processor = create_redaction_processor(extra_fields={"my_secret"})
        assert "my_secret" in processor.fields_to_redact


class TestEmailMasking:
    """Tests for email masking function."""

    @pytest.fixture
    def processor(self) -> RedactionProcessor:
        return RedactionProcessor()

    def test_standard_email(self, processor: RedactionProcessor) -> None:
        event = {"event": "admin@example.com"}
        result = processor(None, None, event)
        assert "ad***@example.com" in result["event"]

    def test_short_local_part(self, processor: RedactionProcessor) -> None:
        event = {"event": "ab@example.com"}
        result = processor(None, None, event)
        assert "@example.com" in result["event"]

    def test_multiple_emails(self, processor: RedactionProcessor) -> None:
        event = {"event": "From: a@x.com To: b@y.com"}
        result = processor(None, None, event)
        assert "a@x.com" not in result["event"]
        assert "b@y.com" not in result["event"]


class TestCreditCardMasking:
    """Tests for credit card masking."""

    @pytest.fixture
    def processor(self) -> RedactionProcessor:
        return RedactionProcessor()

    def test_with_dashes(self, processor: RedactionProcessor) -> None:
        event = {"event": "4111-1111-1111-1234"}
        result = processor(None, None, event)
        assert "****-****-****-1234" in result["event"]

    def test_with_spaces(self, processor: RedactionProcessor) -> None:
        event = {"event": "4111 1111 1111 5678"}
        result = processor(None, None, event)
        assert "5678" in result["event"]
        assert "4111" not in result["event"]

    def test_continuous(self, processor: RedactionProcessor) -> None:
        event = {"event": "4111111111119999"}
        result = processor(None, None, event)
        assert "9999" in result["event"]

