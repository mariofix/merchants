# Proveedor Genérico

`GenericProvider` se conecta a cualquier gateway de pago que exponga una API REST JSON simple. Configúralo con una URL de checkout y una plantilla de URL de pago.

## Uso

```python
from merchants import Client
from merchants.providers.generic import GenericProvider

provider = GenericProvider(
    checkout_url="https://api.example.com/checkout",
    payment_url_template="https://api.example.com/payments/{payment_id}",
)
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="99.00",
    currency="USD",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
)
print(session.redirect_url)
```

!!! info "Ideal para gateways JSON simples"
    `GenericProvider` funciona bien para gateways que aceptan un cuerpo JSON estándar y devuelven `id` + `redirect_url`. Para flujos más complejos, considera implementar un [proveedor personalizado](custom.md).

## Con Headers Adicionales

Pasa headers estáticos (ej. para auth por API key) con `extra_headers`:

```python
provider = GenericProvider(
    checkout_url="https://api.example.com/checkout",
    payment_url_template="https://api.example.com/payments/{payment_id}",
    extra_headers={"X-API-Key": "mi-clave-secreta"},
)
```

O usa las [estrategias de autenticación](../auth.md) integradas con el `Client`:

```python
from merchants import Client, ApiKeyAuth

client = Client(
    provider=provider,
    auth=ApiKeyAuth("mi-clave-secreta", header="X-API-Key"),
)
```

## Formato de Petición/Respuesta Esperado

### Checkout (POST `checkout_url`)

**Cuerpo de la petición:**

```json
{
  "amount": "99.00",
  "currency": "USD",
  "success_url": "https://example.com/exito",
  "cancel_url": "https://example.com/cancelar",
  "metadata": {}
}
```

**Respuesta esperada:**

```json
{
  "id": "sess_abc123",
  "redirect_url": "https://pay.example.com/sess_abc123"
}
```

### Estado del Pago (GET `payment_url_template`)

**Respuesta esperada:**

```json
{
  "status": "succeeded"
}
```

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `checkout_url` | `str` | requerido | URL completa para enviar peticiones POST de checkout |
| `payment_url_template` | `str` | requerido | Plantilla de URL para GET del estado del pago; `{payment_id}` se reemplaza en tiempo de ejecución |
| `transport` | `Transport \| None` | `None` | Transporte HTTP personalizado |
| `extra_headers` | `dict \| None` | `None` | Headers estáticos añadidos a cada petición |
