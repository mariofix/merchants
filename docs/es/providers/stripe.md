# Proveedor Stripe

`StripeProvider` se integra con la API de Checkout Sessions de Stripe. Convierte los montos a **unidades mínimas** (centavos) según lo requiere Stripe.

!!! note "Implementación de referencia"
    Esta es una implementación de referencia que demuestra el patrón de integración de Stripe. Reemplaza `base_url` e inyecta un transporte real para conectarte a la API de Stripe en producción.

## Instalación

No se requieren dependencias adicionales:

```bash
pip install merchants
```

## Uso

```python
from merchants import Client
from merchants.providers.stripe import StripeProvider

provider = StripeProvider(api_key="sk_test_…")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="19.99",
    currency="USD",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
    metadata={"order_id": "ord_123"},
)
print(session.redirect_url)  # redirige al usuario aquí
```

!!! warning "Usa claves de prueba durante el desarrollo"
    Usa siempre claves `sk_test_…` durante el desarrollo. Nunca guardes claves de producción (`sk_live_…`) en el código fuente — cárgalas desde variables de entorno.

## Manejo de Montos

Stripe requiere montos en la **unidad monetaria más pequeña** (ej. centavos para USD, peniques para GBP). El proveedor convierte automáticamente los montos decimales usando `to_minor_units`:

```python
from merchants import to_minor_units

to_minor_units("19.99")             # 1999 (centavos USD)
to_minor_units("1000", decimals=0)  # 1000 (JPY — sin subdivisión)
```

Las monedas de cero decimales (ej. JPY, BIF, CLP) se manejan automáticamente.

!!! tip "El formato del monto es gestionado automáticamente"
    Pasa los montos como cadenas de texto o `Decimal` en notación decimal estándar (ej. `"19.99"`). El proveedor convierte al entero de unidad mínima correcto de forma automática.

## Estado del Pago

Después de que el usuario completa el checkout, obtén el estado del pago por `payment_id`:

```python
status = client.payments.get("pi_3LHpu2…")

print(status.state)       # PaymentState.SUCCEEDED
print(status.is_final)    # True
print(status.is_success)  # True
```

## Parseo de Webhooks

```python
import merchants

event = merchants.parse_event(payload, provider="stripe")
print(event.event_type)   # ej. "payment_intent.succeeded"
print(event.payment_id)   # ej. "pi_3LHpu2…"
print(event.state)        # PaymentState.SUCCEEDED
```

!!! tip "Verifica antes de parsear"
    Llama siempre a `merchants.verify_signature(...)` antes de `parse_event`. Consulta la guía de [Webhooks](../webhooks.md) para un ejemplo completo de manejador.

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `api_key` | `str` | requerido | Clave secreta de Stripe (`sk_test_…` o `sk_live_…`) |
| `base_url` | `str` | `"https://api.stripe.com"` | Override para pruebas |
| `transport` | `Transport \| None` | `None` | Transporte HTTP personalizado |

## Mapeo de Estados

| Estado Stripe | `PaymentState` |
|---|---|
| `requires_payment_method` | `PENDING` |
| `requires_confirmation` | `PENDING` |
| `requires_action` | `PENDING` |
| `processing` | `PROCESSING` |
| `succeeded` | `SUCCEEDED` |
| `canceled` | `CANCELLED` |
| `failed` | `FAILED` |
