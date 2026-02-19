"""Amount formatting utilities."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def to_decimal_string(amount: Decimal) -> str:
    """Serialize *amount* as a decimal string (e.g., Decimal("19.99") -> "19.99").

    This is the default serialization used by the SDK.
    """
    return str(amount)


def to_minor_units(amount: Decimal, exponent: int = 2) -> int:
    """Convert *amount* to integer minor units (e.g., cents).

    Parameters
    ----------
    amount:
        The monetary amount as a :class:`~decimal.Decimal`.
    exponent:
        Number of decimal places for the currency's minor unit.
        For most currencies (USD, EUR, …) this is ``2`` (cents).
        For zero-decimal currencies (JPY, …) use ``0``.

    Examples
    --------
    >>> to_minor_units(Decimal("19.99"))
    1999
    >>> to_minor_units(Decimal("19.99"), exponent=2)
    1999
    >>> to_minor_units(Decimal("100"), exponent=0)
    100
    """
    multiplier = Decimal(10) ** exponent
    return int((amount * multiplier).to_integral_value(rounding=ROUND_HALF_UP))
