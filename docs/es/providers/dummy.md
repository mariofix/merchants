# Proveedor de Prueba (Dummy)

`DummyProvider` es un proveedor sin operación real para **desarrollo local y pruebas**. Genera datos aleatorios y nunca hace llamadas HTTP reales.

## Uso

```python
from merchants import Client
from merchants.providers.dummy import DummyProvider

client = Client(provider=DummyProvider())

session = client.payments.create_checkout(
    amount="49.99",
    currency="USD",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
)
print("ID de sesión  :", session.session_id)
print("URL de redirección:", session.redirect_url)

status = client.payments.get(session.session_id)
print("Estado       :", status.state)
```

!!! danger "No usar en producción"
    `DummyProvider` no procesa pagos reales. Usarlo en un entorno en vivo causará que tus usuarios sean redirigidos a una URL falsa y no se realizará ningún cobro.

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `base_url` | `str` | `"https://dummy-pay.example.com"` | URL base falsa usada en la URL de redirección generada |
| `always_state` | `PaymentState \| None` | `None` | Si se establece, cada llamada a `get_payment` retorna este estado en lugar de uno aleatorio |

Usa `always_state` para controlar el resultado en las pruebas:

```python
from merchants.models import PaymentState
from merchants.providers.dummy import DummyProvider

provider = DummyProvider(always_state=PaymentState.SUCCEEDED)
client = Client(provider=provider)

status = client.payments.get("any_id")
assert status.state == PaymentState.SUCCEEDED
```

## Comportamiento

- `create_checkout` devuelve un `CheckoutSession` con un `session_id` aleatorio y una URL de redirección falsa construida a partir de `base_url`.
- `get_payment` devuelve un `PaymentStatus` con un `PaymentState` terminal aleatorio (o `always_state` si está configurado).
- `parse_webhook` devuelve un `WebhookEvent` con `PaymentState.SUCCEEDED` e IDs aleatorios.
- No se requieren credenciales.
- No se realizan llamadas de red.

## Cuándo Usarlo

Usa `DummyProvider` cuando:

- Desarrollas localmente sin credenciales de pago.
- Escribes pruebas unitarias o de integración.
- Prototipas una nueva integración.

!!! tip "Combínalo con pytest"
    En las pruebas, crea un `Client(provider=DummyProvider())` y verifica los objetos `CheckoutSession` y `PaymentStatus` devueltos sin necesidad de simular llamadas HTTP.

!!! warning
    Nunca uses `DummyProvider` en producción. No procesa pagos reales.
