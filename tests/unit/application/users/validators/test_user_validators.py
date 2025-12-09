"""Unit tests for user command validators.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from application.users.commands.mutations.create_user import CreateUserCommand
from application.users.validators.commands import (
    CompositeUserValidator,
    EmailFormatValidator,
    EmailUniquenessValidator,
    PasswordStrengthValidator,
    ValidationError,
    create_user_validator,
)


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_with_message(self) -> None:
        """Should create error with message."""
        error = ValidationError(message="Invalid input")

        assert error.message == "Invalid input"
        assert error.field is None
        assert error.code is None

    def test_create_with_all_fields(self) -> None:
        """Should create error with all fields."""
        error = ValidationError(
            message="Invalid email",
            field="email",
            code="INVALID_EMAIL",
        )

        assert error.message == "Invalid email"
        assert error.field == "email"
        assert error.code == "INVALID_EMAIL"

    def test_str_returns_message(self) -> None:
        """str() should return message."""
        error = ValidationError(message="Test error")

        assert str(error) == "Test error"

    def test_is_value_error(self) -> None:
        """Should be a ValueError."""
        error = ValidationError(message="Test")

        assert isinstance(error, ValueError)


class TestEmailUniquenessValidator:
    """Tests for EmailUniquenessValidator."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def validator(self, mock_repository: AsyncMock) -> EmailUniquenessValidator:
        """Create validator instance."""
        return EmailUniquenessValidator(mock_repository)

    @pytest.mark.asyncio
    async def test_validate_unique_email(
        self, validator: EmailUniquenessValidator, mock_repository: AsyncMock
    ) -> None:
        """Should return Ok for unique email."""
        mock_repository.exists_by_email.return_value = False
        command = CreateUserCommand(email="new@example.com", password="Pass123!")

        result = await validator.validate(command)

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_validate_duplicate_email(
        self, validator: EmailUniquenessValidator, mock_repository: AsyncMock
    ) -> None:
        """Should return Err for duplicate email."""
        mock_repository.exists_by_email.return_value = True
        command = CreateUserCommand(email="existing@example.com", password="Pass123!")

        result = await validator.validate(command)

        assert result.is_err()


class TestEmailFormatValidator:
    """Tests for EmailFormatValidator."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        """Create mock service."""
        return MagicMock()

    @pytest.fixture
    def validator(self, mock_service: MagicMock) -> EmailFormatValidator:
        """Create validator instance."""
        return EmailFormatValidator(mock_service)

    @pytest.mark.asyncio
    async def test_validate_valid_email(
        self, validator: EmailFormatValidator, mock_service: MagicMock
    ) -> None:
        """Should return Ok for valid email format."""
        mock_service.validate_email.return_value = (True, None)
        command = CreateUserCommand(email="valid@example.com", password="Pass123!")

        result = await validator.validate(command)

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_validate_invalid_email(
        self, validator: EmailFormatValidator, mock_service: MagicMock
    ) -> None:
        """Should return Err for invalid email format."""
        mock_service.validate_email.return_value = (False, "Invalid format")
        command = CreateUserCommand(email="invalid-email", password="Pass123!")

        result = await validator.validate(command)

        assert result.is_err()


class TestPasswordStrengthValidator:
    """Tests for PasswordStrengthValidator."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        """Create mock service."""
        return MagicMock()

    @pytest.fixture
    def validator(self, mock_service: MagicMock) -> PasswordStrengthValidator:
        """Create validator instance."""
        return PasswordStrengthValidator(mock_service)

    @pytest.mark.asyncio
    async def test_validate_strong_password(
        self, validator: PasswordStrengthValidator, mock_service: MagicMock
    ) -> None:
        """Should return Ok for strong password."""
        mock_service.validate_password_strength.return_value = (True, [])
        command = CreateUserCommand(email="test@example.com", password="StrongPass123!")

        result = await validator.validate(command)

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_validate_weak_password(
        self, validator: PasswordStrengthValidator, mock_service: MagicMock
    ) -> None:
        """Should return Err for weak password."""
        mock_service.validate_password_strength.return_value = (
            False,
            ["Too short", "No uppercase"],
        )
        command = CreateUserCommand(email="test@example.com", password="weak")

        result = await validator.validate(command)

        assert result.is_err()


class TestCompositeUserValidator:
    """Tests for CompositeUserValidator."""

    @pytest.mark.asyncio
    async def test_all_validators_pass(self) -> None:
        """Should return Ok when all validators pass."""
        validator1 = AsyncMock()
        validator1.validate = AsyncMock(return_value=MagicMock(is_err=lambda: False))
        validator2 = AsyncMock()
        validator2.validate = AsyncMock(return_value=MagicMock(is_err=lambda: False))

        composite = CompositeUserValidator(validator1, validator2)
        command = CreateUserCommand(email="test@example.com", password="Pass123!")

        result = await composite.validate(command)

        assert result.is_ok()
        validator1.validate.assert_called_once()
        validator2.validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fails_fast_on_first_error(self) -> None:
        """Should fail fast on first validation error."""
        from core.base.patterns.result import Err

        validator1 = AsyncMock()
        validator1.validate = AsyncMock(
            return_value=Err(ValidationError(message="First error"))
        )
        validator2 = AsyncMock()
        validator2.validate = AsyncMock()

        composite = CompositeUserValidator(validator1, validator2)
        command = CreateUserCommand(email="test@example.com", password="Pass123!")

        result = await composite.validate(command)

        assert result.is_err()
        validator1.validate.assert_called_once()
        validator2.validate.assert_not_called()


class TestCreateUserValidator:
    """Tests for create_user_validator factory."""

    def test_creates_composite_validator(self) -> None:
        """Should create CompositeUserValidator with all validators."""
        mock_repository = AsyncMock()
        mock_service = MagicMock()

        validator = create_user_validator(mock_repository, mock_service)

        assert isinstance(validator, CompositeUserValidator)
        assert len(validator._validators) == 3
