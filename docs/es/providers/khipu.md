# Proveedor Khipu

`KhipuProvider` se integra con [Khipu](https://khipu.com), una plataforma de pagos por transferencia bancaria chilena, a través del paquete [`khipu-tools`](https://pypi.org/project/khipu-tools/).

## Instalación

Instala merchants con el extra `khipu`:

```bash
pip install "merchants-sdk[khipu]"
```

!!! note "Requiere khipu-tools"
    El extra `khipu` instala [`khipu-tools`](https://pypi.org/project/khipu-tools/). Si no está instalado, importar `KhipuProvider` lanza un `ImportError` con instrucciones de instalación.

## Uso

```python
from merchants import Client
from merchants.providers.khipu import KhipuProvider

provider = KhipuProvider(
    api_key="TU_API_KEY_DE_RECEPTOR",
    subject="Pedido #456",
    notify_url="https://example.com/webhooks/khipu",
)
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="15000",
    currency="CLP",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
    metadata={"order_id": "ord_456"},
)
print(session.redirect_url)  # redirige al usuario a Khipu aquí
```

## Estado del Pago

```python
status = client.payments.get("PAYMENT_ID_KHIPU")

print(status.state)     # ej. PaymentState.SUCCEEDED
print(status.amount)    # ej. Decimal("15000")
print(status.currency)  # "CLP"
```

## Parseo de Webhooks

`KhipuProvider.parse_webhook` maneja los payloads JSON de Khipu v3.0. Cuando `webhook_secret` está configurado, verifica el header `x-khipu-signature` usando HMAC-SHA256 antes de parsear.

```python
# Usa parse_webhook del proveedor para la verificación de firma
provider = KhipuProvider(
    api_key="TU_API_KEY_DE_RECEPTOR",
    webhook_secret="TU_SECRETO_DE_WEBHOOK",
)
client = Client(provider=provider)

# Accede al proveedor directamente para usar parse_webhook
event = client._provider.parse_webhook(request.body, dict(request.headers))
print(event.event_type)   # "payment.conciliated" o "payment.notification"
print(event.payment_id)   # ID del pago Khipu
print(event.state)        # ej. PaymentState.SUCCEEDED
```

!!! info "Soporta form-encoded y JSON"
    `KhipuProvider.parse_webhook` detecta y maneja automáticamente tanto los cuerpos JSON como los URL-encoded. La API v3.0 envía JSON.

!!! note "Detección del estado a partir de `conciliation_date`"
    En v3.0, el estado del pago se determina por la presencia de `conciliation_date` en el payload. Si está presente, el estado es `SUCCEEDED` y el tipo de evento es `"payment.conciliated"`. De lo contrario, se usa `payment_status` con el mapa de estados estándar.

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `api_key` | `str` | requerido | API key de receptor Khipu |
| `subject` | `str` | `"Order"` | Asunto del pago por defecto enviado a Khipu |
| `notify_url` | `str` | `""` | URL de webhook que Khipu invocará al confirmar el pago |
| `webhook_secret` | `str` | `""` | Secreto de firma del webhook para la verificación HMAC-SHA256 |

## Mapeo de Estados

| Estado Khipu | `PaymentState` |
|---|---|
| `pending` | `PENDING` |
| `verifying` | `PROCESSING` |
| `done` | `SUCCEEDED` |
| `rejected` | `FAILED` |
| `expired` | `CANCELLED` |
| `reversed` | `REFUNDED` |
