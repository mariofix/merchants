# Proveedor PayPal

`PayPalProvider` se integra con la API de Órdenes de PayPal. Envía los montos como **cadenas decimales** (ej. `"19.99"`) según lo requiere PayPal.

!!! note "Implementación de referencia"
    Esta es una implementación de referencia que demuestra el patrón de integración de PayPal. Reemplaza `base_url` e inyecta un transporte real para conectarte a la API de PayPal en producción.

## Instalación

No se requieren dependencias adicionales:

```bash
pip install merchants-sdk
```

## Uso

```python
from merchants import Client
from merchants.providers.paypal import PayPalProvider

provider = PayPalProvider(access_token="ACCESS_TOKEN")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="49.99",
    currency="USD",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
)
print(session.redirect_url)  # redirige al usuario a PayPal aquí
```

!!! info "Los tokens de acceso expiran"
    Los tokens de acceso OAuth de PayPal tienen vida corta. En producción, implementa un mecanismo de renovación de tokens y pasa un token fresco al crear el proveedor.

## Manejo de Montos

PayPal acepta montos como cadenas decimales. El proveedor convierte los montos usando `to_decimal_string`:

```python
from merchants import to_decimal_string

to_decimal_string("49.9")  # "49.90"
to_decimal_string(49)      # "49.00"
```

## Estado del Pago

```python
status = client.payments.get("ORDER_ID")

print(status.state)     # ej. PaymentState.SUCCEEDED
print(status.amount)    # ej. Decimal("49.99")
print(status.currency)  # ej. "USD"
```

## Parseo de Webhooks

```python
import merchants

event = merchants.parse_event(payload, provider="paypal")
print(event.event_type)   # ej. "PAYMENT.CAPTURE.COMPLETED"
print(event.payment_id)   # ej. "ORDER_ID"
print(event.state)        # PaymentState.SUCCEEDED
```

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `access_token` | `str` | requerido | Token de acceso OAuth de PayPal |
| `base_url` | `str` | `"https://api-m.paypal.com"` | Override para pruebas |
| `transport` | `Transport \| None` | `None` | Transporte HTTP personalizado |

!!! tip "Usa el sandbox para pruebas"
    Reemplaza `base_url` con `"https://api-m.sandbox.paypal.com"` y usa credenciales de sandbox para probar sin procesar pagos reales.

## Mapeo de Estados

| Estado PayPal | `PaymentState` |
|---|---|
| `CREATED` | `PENDING` |
| `APPROVED` | `PROCESSING` |
| `COMPLETED` | `SUCCEEDED` |
| `VOIDED` | `CANCELLED` |
| `REFUNDED` | `REFUNDED` |
