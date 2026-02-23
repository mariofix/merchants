# Utilidades de Montos

merchants provee tres funciones utilitarias para el manejo consistente de montos entre proveedores de pago. Los distintos gateways esperan formatos diferentes — estos helpers simplifican la conversión.

## Resumen

| Helper | Entrada de ejemplo | Salida de ejemplo | Caso de uso |
|---|---|---|---|
| `to_decimal_string` | `"19.99"` | `"19.99"` | PayPal, la mayoría de las APIs REST |
| `to_minor_units` | `"19.99"` | `1999` | Stripe (centavos) |
| `from_minor_units` | `1999` | `Decimal("19.99")` | Convertir montos de Stripe de vuelta |

## `to_decimal_string`

Convierte un monto a una cadena decimal canónica con dos decimales. Adecuado para proveedores como PayPal que aceptan cadenas decimales.

```python
from merchants import to_decimal_string
from decimal import Decimal

to_decimal_string("19.99")        # "19.99"
to_decimal_string(Decimal("9.5")) # "9.50"
to_decimal_string(100)            # "100.00"
to_decimal_string(19.999)         # "20.00"  (redondeo half-up)
```

!!! warning "Evita entradas `float`"
    Pasar un `float` (ej. `19.99`) puede introducir imprecisión de punto flotante. Preferí entradas `str` o `Decimal` para resultados exactos.

## `to_minor_units`

Convierte un monto decimal a la unidad monetaria más pequeña (ej. centavos para USD). Adecuado para proveedores como Stripe que requieren enteros en unidades mínimas.

```python
from merchants import to_minor_units

to_minor_units("19.99")              # 1999
to_minor_units("1.005", decimals=2)  # 101  (redondeo half-up)
to_minor_units("1000", decimals=0)   # 1000 (JPY — sin subdivisión)
to_minor_units(Decimal("0.50"))      # 50
```

**Parámetros:**

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `amount` | `Decimal \| int \| float \| str` | requerido | El monto a convertir |
| `decimals` | `int` | `2` | Número de decimales de la moneda (ej. `0` para JPY) |

## `from_minor_units`

Convierte un entero en unidades mínimas de vuelta a un `Decimal`. Útil para leer montos en respuestas de Stripe.

```python
from merchants import from_minor_units
from decimal import Decimal

from_minor_units(1999)               # Decimal("19.99")
from_minor_units(50)                 # Decimal("0.50")
from_minor_units(1000, decimals=0)   # Decimal("1000")
```

**Parámetros:**

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `minor` | `int` | requerido | El entero en unidades mínimas |
| `decimals` | `int` | `2` | Número de decimales de la moneda |

## Redondeo

Todos los helpers usan redondeo `ROUND_HALF_UP` (el estándar para cálculos financieros):

```python
to_decimal_string("19.995")  # "20.00"
to_minor_units("1.005")      # 101
```

## Monedas de Cero Decimales

Para monedas sin subdivisión (ej. JPY), pasa `decimals=0`:

```python
to_minor_units("1000", decimals=0)   # 1000
from_minor_units(1000, decimals=0)   # Decimal("1000")
```

!!! info "Monedas de cero decimales en Stripe"
    `StripeProvider` detecta automáticamente las monedas de cero decimales (JPY, BIF, CLP, etc.) y establece `decimals=0`. Para `GenericProvider` o proveedores personalizados, pasa `decimals` explícitamente.
