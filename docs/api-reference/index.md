# API Reference

Complete API reference for the merchants SDK, generated from source docstrings.

## Modules

| Module | Description |
|---|---|
| [`merchants.client`](client.md) | `Client` and `PaymentsResource` |
| [`merchants.models`](models.md) | Pydantic data models |
| [`merchants.providers`](providers.md) | Provider base class and registry |
| [`merchants.auth`](auth.md) | Auth strategy classes |
| [`merchants.transport`](transport.md) | Transport protocol and `RequestsTransport` |
| [`merchants.amount`](amount.md) | Amount conversion helpers |
| [`merchants.webhooks`](webhooks.md) | Webhook verification and parsing |

## Top-level Exports

All public symbols are re-exported from the top-level `merchants` package:

```python
import merchants

# Client
merchants.Client
merchants.PaymentsResource

# Auth
merchants.ApiKeyAuth
merchants.TokenAuth
merchants.AuthStrategy

# Models
merchants.CheckoutSession
merchants.PaymentState
merchants.PaymentStatus
merchants.WebhookEvent

# Providers
merchants.Provider
merchants.UserError
merchants.register_provider
merchants.get_provider
merchants.list_providers
merchants.normalise_state

# Transport
merchants.RequestsTransport
merchants.HttpResponse
merchants.Transport
merchants.TransportError

# Amount
merchants.to_decimal_string
merchants.to_minor_units
merchants.from_minor_units

# Webhooks
merchants.verify_signature
merchants.parse_event
merchants.WebhookVerificationError
```
