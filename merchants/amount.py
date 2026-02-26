"""Amount handling utilities."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def to_decimal_string(amount: Decimal | int | float | str) -> str:
    """Return a canonical decimal string (e.g. '19.99').

    Suitable for providers like PayPal that accept decimal strings.
    """
    d = Decimal(str(amount))
    # Normalise: strip unnecessary trailing zeros but keep at least 2 dp
    formatted = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(formatted)


def to_minor_units(amount: Decimal | int | float | str, decimals: int = 2) -> int:
    """Convert a decimal amount to the smallest currency unit (e.g. cents).

    Suitable for providers like Stripe that require integer minor-units.

    >>> to_minor_units("19.99")
    1999
    >>> to_minor_units("1.005", decimals=2)
    101
    >>> to_minor_units("100", decimals=0)
    100
    """
    d = Decimal(str(amount))
    factor = Decimal(10) ** decimals
    return int((d * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_minor_units(minor: int, decimals: int = 2) -> Decimal:
    """Convert minor-unit integer back to a Decimal amount.

    >>> from_minor_units(1999)
    Decimal('19.99')
    """
    factor = Decimal(10) ** decimals
    if factor == 0:
        return Decimal(0)
    return (Decimal(minor) / factor).quantize(
        Decimal("0." + "0" * decimals) if decimals > 0 else Decimal("1"),
        rounding=ROUND_HALF_UP,
    )
