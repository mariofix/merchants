# Proveedor Personalizado

Implementa la clase base abstracta `Provider` para integrar cualquier gateway de pago con el SDK merchants.

## Ejemplo Mínimo

```python
from decimal import Decimal
from typing import Any

from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError


class MiProveedor(Provider):
    key = "mi_gateway"

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        # Llama a tu gateway aquí; lanza UserError ante fallos
        return CheckoutSession(
            session_id="sess_1",
            redirect_url="https://pay.mi-gateway.com/sess_1",
            provider=self.key,
            amount=amount,
            currency=currency,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(
            payment_id=payment_id,
            state=PaymentState.PENDING,
            provider=self.key,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        from merchants.webhooks import parse_event
        return parse_event(payload, provider=self.key)
```

## Ejemplo Completo con Llamadas HTTP

Consulta [`examples/03_custom_provider.py`](https://github.com/mariofix/merchnts-cp/blob/main/examples/03_custom_provider.py) para un proveedor completo que:

- Envuelve una API REST JSON con `requests`.
- Lanza `UserError` en respuestas no-2xx.
- Mapea cadenas de estado específicas del proveedor a `PaymentState`.
- Parsea payloads de webhooks entrantes.

## Métodos Requeridos

| Método | Descripción |
|---|---|
| `create_checkout(...)` | Crea una sesión de hosted-checkout; devuelve `CheckoutSession` |
| `get_payment(payment_id)` | Obtiene el estado del pago; devuelve `PaymentStatus` |
| `parse_webhook(payload, headers)` | Parsea bytes de webhook crudos; devuelve `WebhookEvent` |

## Lanzamiento de Errores

Lanza siempre `UserError` (no una excepción genérica) ante fallos del proveedor:

```python
from merchants.providers import UserError

if not resp.ok:
    raise UserError(
        message="Pago rechazado",
        code=str(resp.status_code),
    )
```

!!! warning "Usa `UserError`, no excepciones genéricas"
    El SDK captura `UserError` y lo expone limpiamente a los llamadores. Lanzar una `Exception` o `RuntimeError` genérica puede aparecer inesperadamente como un error 500 en tu aplicación.

## Registro del Proveedor

Registra una instancia del proveedor para que pueda seleccionarse por clave de texto:

```python
from merchants.providers import register_provider

register_provider(MiProveedor())

# Ahora usable por clave
from merchants import Client
client = Client(provider="mi_gateway")
```

!!! note "Las claves deben ser únicas"
    Si llamas a `register_provider` con un proveedor cuya `key` ya está registrada, la nueva instancia reemplaza silenciosamente a la anterior. Usa valores de `key` distintos para evitar conflictos.

## Normalización de Estados

Usa `normalise_state` para convertir cadenas de estado arbitrarias a valores `PaymentState`:

```python
from merchants.providers import normalise_state
from merchants.models import PaymentState

state = normalise_state("paid")     # PaymentState.SUCCEEDED
state = normalise_state("pending")  # PaymentState.PENDING
state = normalise_state("xyzzy")    # PaymentState.UNKNOWN
```

O define tu propio mapeo:

```python
_STATE_MAP = {
    "WAITING": PaymentState.PENDING,
    "APPROVED": PaymentState.SUCCEEDED,
    "DECLINED": PaymentState.FAILED,
}

state = _STATE_MAP.get(raw_status.upper(), normalise_state(raw_status))
```

!!! tip "Prefiere mapeos de estados explícitos"
    Si tu gateway usa cadenas de estado predecibles y documentadas, define un diccionario `_STATE_MAP` explícito como se muestra arriba. Esto hace el mapeo visible, testeable e independiente de la heurística de `normalise_state`.
