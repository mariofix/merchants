# Amount Helpers

merchants provides three utility functions for consistent amount handling across payment providers. Different gateways expect different formats — these helpers make conversion straightforward.

## Overview

| Helper | Example input | Example output | Use case |
|---|---|---|---|
| `to_decimal_string` | `"19.99"` | `"19.99"` | PayPal, most REST APIs |
| `to_minor_units` | `"19.99"` | `1999` | Stripe (cents/pence) |
| `from_minor_units` | `1999` | `Decimal("19.99")` | Converting Stripe amounts back |

## `to_decimal_string`

Converts an amount to a canonical two-decimal-place string. Suitable for providers like PayPal that accept decimal strings.

```python
from merchants import to_decimal_string
from decimal import Decimal

to_decimal_string("19.99")       # "19.99"
to_decimal_string(Decimal("9.5")) # "9.50"
to_decimal_string(100)            # "100.00"
to_decimal_string(19.999)         # "20.00"  (rounds half-up)
```

!!! warning "Avoid `float` inputs"
    Passing a `float` (e.g. `19.99`) can introduce floating-point imprecision. Prefer `str` or `Decimal` inputs for exact results.

## `to_minor_units`

Converts a decimal amount to the smallest currency unit (e.g. cents for USD, pence for GBP). Suitable for providers like Stripe that require integer minor-units.

```python
from merchants import to_minor_units

to_minor_units("19.99")              # 1999
to_minor_units("1.005", decimals=2)  # 101  (rounds half-up)
to_minor_units("1000", decimals=0)   # 1000 (JPY — no subdivision)
to_minor_units(Decimal("0.50"))      # 50
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `amount` | `Decimal \| int \| float \| str` | required | The amount to convert |
| `decimals` | `int` | `2` | Number of decimal places for the currency (e.g. `0` for JPY) |

## `from_minor_units`

Converts a minor-unit integer back to a `Decimal`. Useful for reading Stripe response amounts.

```python
from merchants import from_minor_units
from decimal import Decimal

from_minor_units(1999)          # Decimal("19.99")
from_minor_units(50)            # Decimal("0.50")
from_minor_units(1000, decimals=0)  # Decimal("1000")
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `minor` | `int` | required | The minor-unit integer amount |
| `decimals` | `int` | `2` | Number of decimal places for the currency |

## Rounding

All helpers use `ROUND_HALF_UP` rounding (the standard for financial calculations):

```python
to_decimal_string("19.995")  # "20.00"
to_minor_units("1.005")      # 101
```

## Zero-Decimal Currencies

For currencies with no subdivision (e.g. JPY), pass `decimals=0`:

```python
to_minor_units("1000", decimals=0)   # 1000
from_minor_units(1000, decimals=0)   # Decimal("1000")
```

!!! info "Zero-decimal currencies in Stripe"
    `StripeProvider` automatically detects zero-decimal currencies (JPY, BIF, CLP, etc.) and sets `decimals=0` for you. For `GenericProvider` or custom providers, pass `decimals` explicitly.
