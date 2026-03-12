"""Unit tests for phone number utilities."""
import pytest

from cati.utils.phone import is_valid_e164, normalize_e164


class TestNormalizeE164:
    def test_already_e164(self):
        assert normalize_e164("+15551234567") == "+15551234567"

    def test_10_digit_us_number(self):
        assert normalize_e164("5551234567") == "+15551234567"

    def test_11_digit_with_leading_1(self):
        assert normalize_e164("15551234567") == "+15551234567"

    def test_formatted_us_number(self):
        result = normalize_e164("(555) 123-4567")
        assert result == "+15551234567"

    def test_us_number_with_dashes(self):
        result = normalize_e164("555-123-4567")
        assert result == "+15551234567"

    def test_international_with_plus(self):
        result = normalize_e164("+33612345678")
        assert result == "+33612345678"

    def test_strips_spaces(self):
        result = normalize_e164("+1 555 123 4567")
        assert result == "+15551234567"


class TestIsValidE164:
    def test_valid_us_number(self):
        assert is_valid_e164("+15551234567") is True

    def test_valid_french_number(self):
        assert is_valid_e164("+33612345678") is True

    def test_valid_german_number(self):
        assert is_valid_e164("+4915112345678") is True

    def test_missing_plus(self):
        assert is_valid_e164("15551234567") is False

    def test_too_short(self):
        assert is_valid_e164("+1234567") is False

    def test_too_long(self):
        assert is_valid_e164("+1" + "2" * 15) is False

    def test_starts_with_zero(self):
        assert is_valid_e164("+0551234567") is False

    def test_empty_string(self):
        assert is_valid_e164("") is False
