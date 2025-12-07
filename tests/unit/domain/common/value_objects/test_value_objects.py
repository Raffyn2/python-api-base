"""Tests for value objects module.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.1**
"""

from decimal import Decimal

import pytest

from domain.common.value_objects.value_objects import (
    CurrencyCode,
    Money,
    Percentage,
    Slug,
)


class TestCurrencyCode:
    """Tests for CurrencyCode enum."""

    def test_usd_value(self) -> None:
        """Test USD currency code."""
        assert CurrencyCode.USD.value == "USD"

    def test_eur_value(self) -> None:
        """Test EUR currency code."""
        assert CurrencyCode.EUR.value == "EUR"

    def test_brl_value(self) -> None:
        """Test BRL currency code."""
        assert CurrencyCode.BRL.value == "BRL"


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self) -> None:
        """Test creating money."""
        money = Money(Decimal("29.99"), "USD")
        assert money.amount == Decimal("29.99")
        assert money.currency == "USD"

    def test_default_currency(self) -> None:
        """Test default currency is USD."""
        money = Money(Decimal("10.00"))
        assert money.currency == "USD"

    def test_rounds_to_two_decimals(self) -> None:
        """Test amount is rounded to 2 decimals."""
        money = Money(Decimal("29.999"))
        assert money.amount == Decimal("30.00")

    def test_add(self) -> None:
        """Test adding money."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.50"), "USD")
        result = m1 + m2
        assert result.amount == Decimal("15.50")

    def test_add_different_currency_fails(self) -> None:
        """Test adding different currencies fails."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.00"), "EUR")
        with pytest.raises(ValueError, match="different currencies"):
            m1 + m2

    def test_subtract(self) -> None:
        """Test subtracting money."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("3.50"), "USD")
        result = m1 - m2
        assert result.amount == Decimal("6.50")

    def test_multiply(self) -> None:
        """Test multiplying money."""
        money = Money(Decimal("10.00"), "USD")
        result = money * 2
        assert result.amount == Decimal("20.00")

    def test_multiply_decimal(self) -> None:
        """Test multiplying by decimal."""
        money = Money(Decimal("10.00"), "USD")
        result = money * Decimal("1.5")
        assert result.amount == Decimal("15.00")

    def test_negate(self) -> None:
        """Test negating money."""
        money = Money(Decimal("10.00"), "USD")
        result = -money
        assert result.amount == Decimal("-10.00")

    def test_abs(self) -> None:
        """Test absolute value."""
        money = Money(Decimal("-10.00"), "USD")
        result = abs(money)
        assert result.amount == Decimal("10.00")

    def test_bool_true(self) -> None:
        """Test bool is True for non-zero."""
        money = Money(Decimal("10.00"), "USD")
        assert bool(money) is True

    def test_bool_false(self) -> None:
        """Test bool is False for zero."""
        money = Money(Decimal("0.00"), "USD")
        assert bool(money) is False

    def test_less_than(self) -> None:
        """Test less than comparison."""
        m1 = Money(Decimal("5.00"), "USD")
        m2 = Money(Decimal("10.00"), "USD")
        assert m1 < m2

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal comparison."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("10.00"), "USD")
        assert m1 <= m2

    def test_greater_than(self) -> None:
        """Test greater than comparison."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.00"), "USD")
        assert m1 > m2

    def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal comparison."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("10.00"), "USD")
        assert m1 >= m2

    def test_zero(self) -> None:
        """Test creating zero money."""
        money = Money.zero("EUR")
        assert money.amount == Decimal("0.00")
        assert money.currency == "EUR"

    def test_from_cents(self) -> None:
        """Test creating from cents."""
        money = Money.from_cents(2999, "USD")
        assert money.amount == Decimal("29.99")

    def test_to_cents(self) -> None:
        """Test converting to cents."""
        money = Money(Decimal("29.99"), "USD")
        assert money.to_cents() == 2999

    def test_format_usd(self) -> None:
        """Test formatting USD."""
        money = Money(Decimal("1234.56"), "USD")
        assert money.format() == "$1,234.56"

    def test_format_eur(self) -> None:
        """Test formatting EUR."""
        money = Money(Decimal("1234.56"), "EUR")
        assert money.format() == "€1,234.56"

    def test_format_custom_symbol(self) -> None:
        """Test formatting with custom symbol."""
        money = Money(Decimal("100.00"), "USD")
        assert money.format("¥") == "¥100.00"

    def test_is_frozen(self) -> None:
        """Test money is immutable."""
        money = Money(Decimal("10.00"), "USD")
        with pytest.raises(AttributeError):
            money.amount = Decimal("20.00")


class TestPercentage:
    """Tests for Percentage value object."""

    def test_create_percentage(self) -> None:
        """Test creating percentage."""
        pct = Percentage(15.5)
        assert pct.value == 15.5

    def test_as_factor(self) -> None:
        """Test converting to factor."""
        pct = Percentage(15.0)
        assert pct.as_factor() == 0.15

    def test_negative_fails(self) -> None:
        """Test negative percentage fails."""
        with pytest.raises(ValueError, match="negative"):
            Percentage(-5.0)

    def test_over_100_fails(self) -> None:
        """Test percentage over 100 fails."""
        with pytest.raises(ValueError, match="exceed 100"):
            Percentage(101.0)

    def test_zero_valid(self) -> None:
        """Test zero percentage is valid."""
        pct = Percentage(0.0)
        assert pct.value == 0.0

    def test_100_valid(self) -> None:
        """Test 100 percentage is valid."""
        pct = Percentage(100.0)
        assert pct.value == 100.0

    def test_str(self) -> None:
        """Test string representation."""
        pct = Percentage(15.5)
        assert str(pct) == "15.5%"

    def test_is_frozen(self) -> None:
        """Test percentage is immutable."""
        pct = Percentage(15.0)
        with pytest.raises(AttributeError):
            pct.value = 20.0


class TestSlug:
    """Tests for Slug value object."""

    def test_create_slug(self) -> None:
        """Test creating slug."""
        slug = Slug("hello-world")
        assert slug.value == "hello-world"

    def test_from_text(self) -> None:
        """Test creating from text."""
        slug = Slug.from_text("Hello World!")
        assert slug.value == "hello-world"

    def test_from_text_special_chars(self) -> None:
        """Test from_text handles special characters."""
        slug = Slug.from_text("Hello, World! How are you?")
        assert slug.value == "hello-world-how-are-you"

    def test_empty_fails(self) -> None:
        """Test empty slug fails."""
        with pytest.raises(ValueError, match="empty"):
            Slug("")

    def test_invalid_chars_fails(self) -> None:
        """Test invalid characters fail."""
        with pytest.raises(ValueError, match="Invalid slug"):
            Slug("Hello World")

    def test_starts_with_hyphen_fails(self) -> None:
        """Test starting with hyphen fails."""
        with pytest.raises(ValueError, match="start or end"):
            Slug("-hello")

    def test_ends_with_hyphen_fails(self) -> None:
        """Test ending with hyphen fails."""
        with pytest.raises(ValueError, match="start or end"):
            Slug("hello-")

    def test_consecutive_hyphens_fails(self) -> None:
        """Test consecutive hyphens fail."""
        with pytest.raises(ValueError, match="consecutive"):
            Slug("hello--world")

    def test_str(self) -> None:
        """Test string representation."""
        slug = Slug("hello-world")
        assert str(slug) == "hello-world"

    def test_is_frozen(self) -> None:
        """Test slug is immutable."""
        slug = Slug("hello")
        with pytest.raises(AttributeError):
            slug.value = "world"
