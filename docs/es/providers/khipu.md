# Proveedor Khipu

`KhipuProvider` se integra con [Khipu](https://khipu.com), una plataforma de pagos por transferencia bancaria chilena, a través del paquete [`khipu-tools`](https://pypi.org/project/khipu-tools/).

## Instalación

Instala merchants con el extra `khipu`:

```bash
pip install "merchants[khipu]"
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

Khipu envía payloads `application/x-www-form-urlencoded` o JSON. Ambos se manejan automáticamente:

```python
import merchants

event = merchants.parse_event(payload, provider="khipu")
print(event.event_type)   # "payment.notification"
print(event.payment_id)   # ID del pago Khipu
print(event.state)        # ej. PaymentState.SUCCEEDED
```

!!! info "Soporta form-encoded y JSON"
    Khipu puede enviar el cuerpo en JSON o como formulario URL-encoded dependiendo de la versión de la API. `KhipuProvider.parse_webhook` detecta y maneja ambos formatos automáticamente.

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `api_key` | `str` | requerido | API key de receptor Khipu |
| `subject` | `str` | `"Order"` | Asunto del pago por defecto enviado a Khipu |
| `notify_url` | `str` | `""` | URL de webhook que Khipu llamará al confirmar el pago |

## Mapeo de Estados

| Estado Khipu | `PaymentState` |
|---|---|
| `pending` | `PENDING` |
| `verifying` | `PROCESSING` |
| `done` | `SUCCEEDED` |
| `rejected` | `FAILED` |
| `expired` | `CANCELLED` |
| `reversed` | `REFUNDED` |
