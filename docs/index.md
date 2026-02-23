# merchants

*Framework-agnostic hosted-checkout payment SDK for Python. Simple, fast, and provider-independent.*

---

**merchants** is a Python SDK for integrating hosted-checkout payment flows into any web framework. Your server never touches card data — you redirect the user to a provider-hosted payment page.

!!! tip "Just getting started?"
    Jump straight to the [Quick Start](quickstart.md) guide for a working example in under five minutes.

## Key Features

- **Hosted checkout only** — redirect users to a provider-hosted payment page; no card data ever touches your server.
- **Built-in providers** — Stripe, PayPal, [Flow.cl](https://www.flow.cl) and [Khipu](https://khipu.com), plus a `DummyProvider` for local dev.
- **Pluggable transport** — default `requests.Session` backend; inject any `Transport` for testing or custom HTTP clients.
- **Flexible auth** — API-key header auth and Bearer token auth strategies.
- **Pydantic models** — `CheckoutSession`, `PaymentStatus`, `WebhookEvent` with full type hints.
- **Amount helpers** — `to_decimal_string`, `to_minor_units`, `from_minor_units`.
- **Webhook utilities** — HMAC-SHA256 constant-time signature verification and best-effort event parsing.

---

## Quick Example

```python
import merchants
from merchants.providers.stripe import StripeProvider

# 1. Create a provider
stripe = StripeProvider(api_key="sk_test_…")

# 2. Create a client
client = merchants.Client(provider=stripe)

# 3. Create a hosted checkout session
session = client.payments.create_checkout(
    amount="19.99",
    currency="USD",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    metadata={"order_id": "ord_123"},
)
print(session.redirect_url)  # redirect your user here
```

!!! note "No card data on your server"
    merchants only supports hosted-checkout flows. Card details are entered on the provider's page and never pass through your application.

---

## Supported Providers

| Provider | Key | Install extra | Notes |
|---|---|---|---|
| `StripeProvider` | `"stripe"` | – | Minor-unit amounts (cents) |
| `PayPalProvider` | `"paypal"` | – | Decimal-string amounts |
| `FlowProvider` | `"flow"` | `merchants[flow]` | Flow.cl (Chile) via `pyflowcl` |
| `KhipuProvider` | `"khipu"` | `merchants[khipu]` | Khipu (Chile) via `khipu-tools` |
| `GenericProvider` | `"generic"` | – | Configurable REST endpoints |
| `DummyProvider` | `"dummy"` | – | Random data, no API calls |

---

## Installation

```bash
pip install merchants
```

See the [Installation](installation.md) page for all options including optional provider extras.

---

## License

MIT
