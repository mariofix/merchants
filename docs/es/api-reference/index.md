# Referencia de API

Referencia completa de la API del SDK merchants, generada a partir de los docstrings del código fuente.

## Módulos

| Módulo | Descripción |
|---|---|
| [`merchants.client`](client.md) | `Client` y `PaymentsResource` |
| [`merchants.models`](models.md) | Modelos de datos Pydantic |
| [`merchants.providers`](providers.md) | Clase base de proveedores y registro |
| [`merchants.auth`](auth.md) | Clases de estrategias de autenticación |
| [`merchants.transport`](transport.md) | Protocolo Transport y `RequestsTransport` |
| [`merchants.amount`](amount.md) | Helpers de conversión de montos |
| [`merchants.webhooks`](webhooks.md) | Verificación y parseo de webhooks |

## Exportaciones de Nivel Superior

Todos los símbolos públicos se re-exportan desde el paquete `merchants` de nivel superior:

```python
import merchants

# Cliente
merchants.Client
merchants.PaymentsResource

# Autenticación
merchants.ApiKeyAuth
merchants.TokenAuth
merchants.AuthStrategy

# Modelos
merchants.CheckoutSession
merchants.PaymentState
merchants.PaymentStatus
merchants.WebhookEvent

# Proveedores
merchants.Provider
merchants.UserError
merchants.register_provider
merchants.get_provider
merchants.list_providers
merchants.normalise_state

# Transporte
merchants.RequestsTransport
merchants.HttpResponse
merchants.Transport
merchants.TransportError

# Montos
merchants.to_decimal_string
merchants.to_minor_units
merchants.from_minor_units

# Webhooks
merchants.verify_signature
merchants.parse_event
merchants.WebhookVerificationError
```
