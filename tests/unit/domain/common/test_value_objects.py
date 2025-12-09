"""Unit tests for domain/common/value_objects/value_objects.py.

Tests Money, Percentage, and Slug value objects.

**Feature: test-coverage-90-percent**
**Validates: Requirements 2.1**
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

    def test_common_currencies_exist(self) -> None:
        """Common currency codes should exist."""
        assert CurrencyCode.USD.value == "USD"
        assert CurrencyCode.EUR.value == "EUR"
        assert CurrencyCode.GBP.value == "GBP"
        assert CurrencyCode.BRL.value == "BRL"


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self) -> None:
        """Money should store amount and currency."""
        money = Money(Decimal("29.99"), "USD")
        
        assert money.amount == Decimal("29.99")
        assert money.currency == "USD"

    def test_create_money_from_float(self) -> None:
        """Money should convert float to Decimal."""
        money = Money(29.99, "USD")  # type: ignore
        
        assert isinstance(money.amount, Decimal)
        assert money.amount == Decimal("29.99")

    def test_create_money_from_int(self) -> None:
        """Money should convert int to Decimal."""
        money = Money(30, "USD")  # type: ignore
        
        assert money.amount == Decimal("30.00")

    def test_money_rounds_to_two_decimals(self) -> None:
        """Money should round to 2 decimal places."""
        money = Money(Decimal("29.999"), "USD")
        
        assert money.amount == Decimal("30.00")

    def test_money_default_currency(self) -> None:
        """Money should default to USD."""
        money = Money(Decimal("10"))
        
        assert money.currency == "USD"

    def test_money_addition(self) -> None:
        """Money addition should work."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.50"), "USD")
        
        result = m1 + m2
        
        assert result.amount == Decimal("15.50")
        assert result.currency == "USD"

    def test_money_addition_different_currency_raises(self) -> None:
        """Money addition with different currencies should raise."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.50"), "EUR")
        
        with pytest.raises(ValueError, match="different currencies"):
            m1 + m2

    def test_money_subtraction(self) -> None:
        """Money subtraction should work."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("3.50"), "USD")
        
        result = m1 - m2
        
        assert result.amount == Decimal("6.50")

    def test_money_multiplication(self) -> None:
        """Money multiplication should work."""
        money = Money(Decimal("10.00"), "USD")
        
        result = money * 3
        
        assert result.amount == Decimal("30.00")

    def test_money_multiplication_float(self) -> None:
        """Money multiplication with float should work."""
        money = Money(Decimal("10.00"), "USD")
        
        result = money * 1.5
        
        assert result.amount == Decimal("15.00")

    def test_money_negation(self) -> None:
        """Money negation should work."""
        money = Money(Decimal("10.00"), "USD")
        
        result = -money
        
        assert result.amount == Decimal("-10.00")

    def test_money_abs(self) -> None:
        """Money abs should work."""
        money = Money(Decimal("-10.00"), "USD")
        
        result = abs(money)
        
        assert result.amount == Decimal("10.00")

    def test_money_bool_nonzero(self) -> None:
        """Non-zero money should be truthy."""
        money = Money(Decimal("10.00"), "USD")
        
        assert bool(money) is True

    def test_money_bool_zero(self) -> None:
        """Zero money should be falsy."""
        money = Money(Decimal("0"), "USD")
        
        assert bool(money) is False

    def test_money_comparison_lt(self) -> None:
        """Money less than comparison should work."""
        m1 = Money(Decimal("5.00"), "USD")
        m2 = Money(Decimal("10.00"), "USD")
        
        assert m1 < m2
        assert not m2 < m1

    def test_money_comparison_le(self) -> None:
        """Money less than or equal comparison should work."""
        m1 = Money(Decimal("5.00"), "USD")
        m2 = Money(Decimal("5.00"), "USD")
        
        assert m1 <= m2

    def test_money_comparison_gt(self) -> None:
        """Money greater than comparison should work."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("5.00"), "USD")
        
        assert m1 > m2

    def test_money_comparison_ge(self) -> None:
        """Money greater than or equal comparison should work."""
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("10.00"), "USD")
        
        assert m1 >= m2

    def test_money_zero(self) -> None:
        """Money.zero should create zero amount."""
        money = Money.zero("EUR")
        
        assert money.amount == Decimal("0")
        assert money.currency == "EUR"

    def test_money_from_cents(self) -> None:
        """Money.from_cents should convert cents to dollars."""
        money = Money.from_cents(2999, "USD")
        
        assert money.amount == Decimal("29.99")

    def test_money_to_cents(self) -> None:
        """Money.to_cents should convert to cents."""
        money = Money(Decimal("29.99"), "USD")
        
        assert money.to_cents() == 2999

    def test_money_format_usd(self) -> None:
        """Money.format should format USD correctly."""
        money = Money(Decimal("1234.56"), "USD")
        
        assert money.format() == "$1,234.56"

    def test_money_format_eur(self) -> None:
        """Money.format should format EUR correctly."""
        money = Money(Decimal("1234.56"), "EUR")
        
        assert money.format() == "€1,234.56"

    def test_money_format_custom_symbol(self) -> None:
        """Money.format should accept custom symbol."""
        money = Money(Decimal("100.00"), "USD")
        
        assert money.format("US$") == "US$100.00"

    def test_money_immutable(self) -> None:
        """Money should be immutable."""
        money = Money(Decimal("10.00"), "USD")
        
        with pytest.raises(AttributeError):
            money.amount = Decimal("20.00")  # type: ignore


class TestPercentage:
    """Tests for Percentage value object."""

    def test_create_percentage(self) -> None:
        """Percentage should store value."""
        pct = Percentage(15.5)
        
        assert pct.value == 15.5

    def test_percentage_as_factor(self) -> None:
        """as_factor should convert to decimal."""
        pct = Percentage(15.5)
        
        assert pct.as_factor() == 0.155

    def test_percentage_str(self) -> None:
        """str should format with % symbol."""
        pct = Percentage(15.5)
        
        assert str(pct) == "15.5%"

    def test_percentage_negative_raises(self) -> None:
        """Negative percentage should raise."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Percentage(-5)

    def test_percentage_over_100_raises(self) -> None:
        """Percentage over 100 should raise."""
        with pytest.raises(ValueError, match="cannot exceed 100"):
            Percentage(101)

    def test_percentage_zero(self) -> None:
        """Zero percentage should be valid."""
        pct = Percentage(0)
        
        assert pct.value == 0
        assert pct.as_factor() == 0

    def test_percentage_100(self) -> None:
        """100% should be valid."""
        pct = Percentage(100)
        
        assert pct.value == 100
        assert pct.as_factor() == 1.0


class TestSlug:
    """Tests for Slug value object."""

    def test_create_slug(self) -> None:
        """Slug should store value."""
        slug = Slug("hello-world")
        
        assert slug.value == "hello-world"

    def test_slug_str(self) -> None:
        """str should return value."""
        slug = Slug("hello-world")
        
        assert str(slug) == "hello-world"

    def test_slug_from_text(self) -> None:
        """from_text should convert text to slug."""
        slug = Slug.from_text("Hello World!")
        
        assert slug.value == "hello-world"

    def test_slug_from_text_special_chars(self) -> None:
        """from_text should handle special characters."""
        slug = Slug.from_text("Hello, World! How are you?")
        
        assert slug.value == "hello-world-how-are-you"

    def test_slug_from_text_numbers(self) -> None:
        """from_text should preserve numbers."""
        slug = Slug.from_text("Product 123")
        
        assert slug.value == "product-123"

    def test_slug_empty_raises(self) -> None:
        """Empty slug should raise."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Slug("")

    def test_slug_invalid_chars_raises(self) -> None:
        """Slug with invalid chars should raise."""
        with pytest.raises(ValueError, match="Invalid slug format"):
            Slug("Hello World")

    def test_slug_starts_with_hyphen_raises(self) -> None:
        """Slug starting with hyphen should raise."""
        with pytest.raises(ValueError, match="cannot start or end with hyphen"):
            Slug("-hello")

    def test_slug_ends_with_hyphen_raises(self) -> None:
        """Slug ending with hyphen should raise."""
        with pytest.raises(ValueError, match="cannot start or end with hyphen"):
            Slug("hello-")

    def test_slug_consecutive_hyphens_raises(self) -> None:
        """Slug with consecutive hyphens should raise."""
        with pytest.raises(ValueError, match="consecutive hyphens"):
            Slug("hello--world")

    def test_slug_valid_with_numbers(self) -> None:
        """Slug with numbers should be valid."""
        slug = Slug("product-123-abc")
        
        assert slug.value == "product-123-abc"
