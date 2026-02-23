"""Tests for amount formatting utilities."""
from decimal import Decimal

import pytest

from merchants.amount import from_minor_units, to_decimal_string, to_minor_units


class TestToDecimalString:
    def test_integer(self):
        assert to_decimal_string(19) == "19.00"

    def test_float(self):
        assert to_decimal_string(19.99) == "19.99"

    def test_decimal(self):
        assert to_decimal_string(Decimal("9.50")) == "9.50"

    def test_string(self):
        assert to_decimal_string("100.00") == "100.00"

    def test_zero(self):
        assert to_decimal_string(0) == "0.00"

    def test_large(self):
        assert to_decimal_string("1234567.89") == "1234567.89"

    def test_rounds_half_up(self):
        # 0.005 should round to 0.01
        assert to_decimal_string("0.005") == "0.01"


class TestToMinorUnits:
    def test_standard_two_decimals(self):
        assert to_minor_units("19.99") == 1999

    def test_whole_amount(self):
        assert to_minor_units("100") == 10000

    def test_zero_decimal_currency(self):
        assert to_minor_units("100", decimals=0) == 100

    def test_three_decimal_currency(self):
        assert to_minor_units("19.999", decimals=3) == 19999

    def test_rounding(self):
        # 1.005 * 100 = 100.5, rounds to 101
        assert to_minor_units("1.005", decimals=2) == 101

    def test_decimal_input(self):
        assert to_minor_units(Decimal("9.99")) == 999

    def test_float_input(self):
        assert to_minor_units(9.99) == 999


class TestFromMinorUnits:
    def test_standard(self):
        assert from_minor_units(1999) == Decimal("19.99")

    def test_zero_decimal(self):
        assert from_minor_units(100, decimals=0) == Decimal("100")

    def test_round_trip(self):
        original = Decimal("42.50")
        assert from_minor_units(to_minor_units(original)) == original
