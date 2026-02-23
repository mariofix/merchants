# Webhooks

merchants provee utilidades para verificar firmas de webhooks y parsear eventos normalizados de los proveedores de pago.

## Verificación de Firma

Usa `verify_signature` para confirmar que un webhook proviene de tu proveedor mediante comparación HMAC-SHA256 en tiempo constante. Esto previene ataques de temporización.

```python
import merchants

try:
    merchants.verify_signature(
        payload=request.body,          # bytes crudos
        secret="whsec_…",
        signature=request.headers["Stripe-Signature"],
    )
except merchants.WebhookVerificationError:
    # Rechaza la petición — la firma es inválida
    return 400
```

!!! danger "Nunca omitas la verificación de firma"
    Sin verificación, cualquiera que conozca la URL de tu endpoint de webhook puede enviar notificaciones falsas de pago exitoso. Siempre verifica antes de procesar.

### Parámetros

| Parámetro | Tipo | Descripción |
|---|---|---|
| `payload` | `bytes` | Cuerpo crudo de la petición |
| `secret` | `str` | Secreto de webhook del panel de tu proveedor |
| `signature` | `str` | Valor del header de firma en la petición entrante |

### `WebhookVerificationError`

Se lanza cuando el HMAC calculado no coincide con la firma proporcionada:

```python
from merchants import WebhookVerificationError

try:
    merchants.verify_signature(payload, secret, signature)
except WebhookVerificationError as e:
    print(e)  # "invalid webhook signature"
```

## Parseo de Eventos

Usa `parse_event` para parsear un payload de webhook crudo en un `WebhookEvent` normalizado:

```python
import merchants

event = merchants.parse_event(request.body, provider="stripe")

print(event.event_type)  # ej. "payment_intent.succeeded"
print(event.state)       # ej. PaymentState.SUCCEEDED
print(event.payment_id)  # ej. "pi_3LHpu2…"
print(event.provider)    # "stripe"
```

!!! note "Parseo de mejor esfuerzo"
    `parse_event` hace una conversión de mejor esfuerzo del payload crudo a un `WebhookEvent`. Los tipos de evento desconocidos o los estados no reconocidos resultan en `state=PaymentState.UNKNOWN`. Consulta `event.raw` para el payload original completo.

### Parámetros

| Parámetro | Tipo | Descripción |
|---|---|---|
| `payload` | `bytes` | Cuerpo crudo del webhook |
| `provider` | `str` | Clave del proveedor (ej. `"stripe"`, `"paypal"`) |

### Campos de `WebhookEvent`

| Campo | Tipo | Descripción |
|---|---|---|
| `event_id` | `str \| None` | ID de evento asignado por el proveedor |
| `event_type` | `str` | Cadena de tipo de evento específica del proveedor |
| `payment_id` | `str \| None` | ID del pago asociado |
| `state` | `PaymentState` | Estado de pago normalizado |
| `provider` | `str` | Clave del proveedor |
| `raw` | `dict` | Payload original parseado para campos específicos del proveedor |

## Ejemplo Completo de Manejador de Webhook

Aquí hay un manejador de webhook completo usando pseudocódigo estilo Django:

```python
import merchants
from merchants import WebhookVerificationError

def webhook_view(request):
    # 1. Verifica la firma
    try:
        merchants.verify_signature(
            payload=request.body,
            secret=settings.STRIPE_WEBHOOK_SECRET,
            signature=request.headers.get("Stripe-Signature", ""),
        )
    except WebhookVerificationError:
        return HttpResponse(status=400)

    # 2. Parsea el evento
    event = merchants.parse_event(request.body, provider="stripe")

    # 3. Maneja según el estado
    if event.state == merchants.PaymentState.SUCCEEDED:
        fulfill_order(event.payment_id)
    elif event.state == merchants.PaymentState.FAILED:
        notify_failure(event.payment_id)

    return HttpResponse(status=200)
```

## Uso del `parse_webhook` del Proveedor

Para parseo específico del proveedor (incluyendo los mapas de estados definidos en el proveedor), usa el método propio del proveedor a través del cliente:

```python
# Accede al proveedor directamente si es necesario
provider = client._provider
event = provider.parse_webhook(request.body, dict(request.headers))
```

!!! tip "Usa `event.raw` para campos específicos del proveedor"
    El campo `WebhookEvent.raw` contiene el payload original parseado. Accede a él cuando necesites campos específicos del proveedor que no están cubiertos por el modelo normalizado.
