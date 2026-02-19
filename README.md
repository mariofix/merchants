# Merchants

This project is under development, not for production use.

[![PyPI version](https://badge.fury.io/py/merchants.svg)](https://badge.fury.io/py/merchants)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/merchants.svg)](https://pypi.org/project/merchants/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A framework-agnostic Python SDK for hosted-checkout payment flows.  Supports
pluggable payment providers (Stripe, PayPal, …), pydantic models, HMAC webhook
verification, and flexible amount formatting.

## Requirements

- Python >= 3.10
- `pydantic >= 2.0`
- `requests >= 2.28` (default HTTP transport; pluggable)

## Installation

```bash
pip install merchants
# or with poetry
poetry add merchants
```

---

## Quick Start

### 1. Choose a provider

```python
from decimal import Decimal
from merchants.client import MerchantsClient
from merchants.providers.mock import MockProvider

# Use the built-in mock provider (no network, great for tests)
client = MerchantsClient(provider="mock")

# Or use a provider instance directly
client = MerchantsClient(provider=MockProvider())
```

### 2. Create a hosted-checkout session

```python
session = client.create_checkout(
    amount=Decimal("49.99"),
    currency="USD",
    return_url="https://example.com/payment/return",
)

print(session.id)           # "mock_a1b2c3d4..."
print(session.redirect_url) # "https://mock.example.com/pay/mock_..."

# Redirect your user to session.redirect_url
```

### 3. Fetch payment status

```python
status = client.get_payment(session.id)
print(status.state)       # PaymentState.SUCCEEDED
print(status.is_final)    # True
print(status.is_success)  # True
```

---

## Provider selection

### Using the built-in registry

```python
from merchants.providers import registry
from merchants.providers.mock import MockProvider
from merchants.providers.stripe import StripeProvider
from merchants.client import MerchantsClient

# Register providers by name
registry.register("mock", MockProvider())
registry.register("stripe", StripeProvider(api_key="sk_test_..."))

# Select by name at runtime
client = MerchantsClient(provider="stripe")
```

### Registering a custom provider

```python
from merchants.providers.base import BaseProvider
from merchants.payments import CheckoutSession, PaymentStatus, PaymentState
from decimal import Decimal

class MyProvider(BaseProvider):
    def create_checkout(self, amount, currency, *, return_url, **kwargs):
        # call your PSP API here
        return CheckoutSession(id="my_id", redirect_url="https://...", raw={})

    def get_payment(self, payment_id):
        return PaymentStatus(id=payment_id, state=PaymentState.SUCCEEDED)

registry.register("mypsp", MyProvider())
client = MerchantsClient(provider="mypsp")
```

---

## Amount formatting

The SDK accepts `Decimal` amounts in the public API.

| Format | Example | Used by |
|---|---|---|
| Decimal string (default) | `"19.99"` | PayPal, most REST APIs |
| Minor units (cents) | `1999` | Stripe |

```python
from decimal import Decimal
from merchants.amount import to_decimal_string, to_minor_units

to_decimal_string(Decimal("19.99"))        # "19.99"
to_minor_units(Decimal("19.99"))           # 1999  (exponent=2 default)
to_minor_units(Decimal("500"), exponent=0) # 500   (zero-decimal, e.g. JPY)
```

Provider implementations decide which format to use internally.

---

## Webhook verification and parsing

```python
from merchants.webhook import verify_signature, parse_event
from merchants.errors import WebhookVerificationError
from merchants.result import Success, Failure

# --- Verify HMAC-SHA256 signature (raises on failure) ---
raw_body: bytes = request.body          # your framework's raw body
signature: str  = request.headers["X-Webhook-Signature"]

try:
    verify_signature(raw_body, signature, secret="your_webhook_secret")
except WebhookVerificationError:
    return 400  # reject the request

# --- Parse the event ---
result = parse_event(raw_body)
if isinstance(result, Success):
    event = result.value
    print(event.event_type)     # "payment.succeeded"
    print(event.payment_id)     # "pay_123"
    print(event.state)          # PaymentState.SUCCEEDED
else:
    print("Parse failed:", result.error)
```

The signature header name is configurable by the integrator; the core
`verify_signature` function accepts the signature string directly so any
framework can read the appropriate header.

---

## Transport and auth (pluggable)

```python
from merchants.transport import RequestsTransport  # default
from merchants.auth import BearerTokenAuth, ApiKeyAuth

client = MerchantsClient(
    provider="mock",
    transport=RequestsTransport(),        # or your own BaseTransport subclass
    auth=BearerTokenAuth("my_token"),     # or ApiKeyAuth("X-Api-Key", "key")
)
```

---

## Package structure

```
merchants/
├── __init__.py          # public API re-exports
├── amount.py            # amount formatting utilities
├── auth.py              # auth strategy helpers
├── client.py            # MerchantsClient
├── errors.py            # SDK error types
├── payments.py          # CheckoutSession, PaymentStatus, PaymentState
├── providers/
│   ├── __init__.py      # ProviderRegistry + default registry instance
│   ├── base.py          # BaseProvider abstract class
│   ├── mock.py          # MockProvider (no network)
│   ├── stripe.py        # StripeProvider scaffold
│   └── paypal.py        # PayPalProvider scaffold
├── result.py            # Success / Failure result types
├── transport.py         # BaseTransport + RequestsTransport
└── webhook.py           # verify_signature, parse_event, WebhookEvent
```

---

## Running tests

```bash
pip install pytest pydantic requests
pytest tests/test_sdk.py -v
```

---

## License

Merchants is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

This project was inspired by the [django-payments](https://github.com/jazzband/django-payments) library.

## Changelog

See the [CHANGELOG](CHANGELOG) file for more details.
