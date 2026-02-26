# merchants

A framework-agnostic Python SDK for hosted-checkout payment flows.

## Features

- **Hosted checkout only** – redirect users to a provider-hosted payment page; no card data ever touches your server.
- **Built-in providers** – Stripe, PayPal, [Flow.cl](https://www.flow.cl) (`pip install merchants[flow]`), [Khipu](https://khipu.com) (`pip install merchants[khipu]`), and a `DummyProvider` for local dev.
- **Provider metadata** – every provider exposes `name`, `author`, `version`, `description`, and `url` via `ProviderInfo` (Pydantic model), enabling downstream applications to inspect and parse the registry.
- **CLI** – a Typer-powered command-line interface for listing providers and inspecting their metadata (`pip install "merchants[cli]"`).
- **Pluggable transport** – default `requests.Session` backend; inject any `Transport` (e.g. httpx) for testing or custom HTTP clients.
- **Flexible auth** – API-key header auth and token (Bearer) auth strategies.
- **Pydantic models** – `CheckoutSession`, `PaymentStatus`, `WebhookEvent` with full type hints.
- **Amount helpers** – `to_decimal_string`, `to_minor_units`, `from_minor_units`.
- **Webhook utilities** – HMAC-SHA256 constant-time signature verification and best-effort event parsing.

## Requirements

- Python ≥ 3.10
- `pydantic >= 2.0`
- `requests >= 2.28`

## Installation

```bash
pip install merchants              # core (Stripe + PayPal stubs)
pip install "merchants[flow]"      # + Flow.cl via pyflowcl
pip install "merchants[khipu]"     # + Khipu via khipu-tools
pip install "merchants[cli]"       # + CLI (typer)
pip install -e ".[dev]"            # local development
```

## Quick Start

```python
import merchants
from merchants.providers.stripe import StripeProvider

# 1. Create a provider
stripe = StripeProvider(api_key="sk_test_…")

# 2. Create a client (accepts provider instance or registered key string)
client = merchants.Client(provider=stripe)

# 3. Create a hosted checkout session – raises UserError on failure
try:
    session = client.payments.create_checkout(
        amount="19.99",
        currency="USD",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        metadata={"order_id": "ord_123"},
    )
    print(session.redirect_url)  # redirect your user here
except merchants.UserError as e:
    print("Payment error:", e)
```

## Providers

| Provider | Key | Install extra | Notes |
|---|---|---|---|
| `StripeProvider` | `"stripe"` | – | Minor-unit amounts (cents) |
| `PayPalProvider` | `"paypal"` | – | Decimal-string amounts |
| `FlowProvider` | `"flow"` | `merchants[flow]` | Flow.cl (Chile) via `pyflowcl` |
| `KhipuProvider` | `"khipu"` | `merchants[khipu]` | Khipu (Chile) via `khipu-tools` |
| `GenericProvider` | `"generic"` | – | Configurable REST endpoints |
| `DummyProvider` | `"dummy"` | – | Random data, no API calls |

```python
# Stripe
from merchants.providers.stripe import StripeProvider
client = Client(provider=StripeProvider(api_key="sk_test_…"))

# PayPal
from merchants.providers.paypal import PayPalProvider
client = Client(provider=PayPalProvider(access_token="token_…"))

# Flow.cl  (pip install merchants[flow])
from merchants.providers.flow import FlowProvider
client = Client(provider=FlowProvider(api_key="…", api_secret="…"))

# Khipu  (pip install merchants[khipu])
from merchants.providers.khipu import KhipuProvider
client = Client(provider=KhipuProvider(api_key="…"))

# Dummy – no credentials, random data for local dev
from merchants.providers.dummy import DummyProvider
client = Client(provider=DummyProvider())
```

## Provider Selection

### By instance

```python
from merchants import Client
from merchants.providers.paypal import PayPalProvider

client = Client(provider=PayPalProvider(access_token="token_…"))
```

### By string key (registry)

```python
from merchants import Client, register_provider
from merchants.providers.stripe import StripeProvider

# Register once at startup
register_provider(StripeProvider(api_key="sk_test_…"))

# Later, select by key
client = Client(provider="stripe")
```

### List registered providers

```python
from merchants import list_providers

print(list_providers())   # ['stripe', 'paypal', ...]
```

### Custom provider

See `examples/03_custom_provider.py` for a full example.

```python
from merchants.providers import Provider, UserError
from merchants.models import CheckoutSession, PaymentStatus, PaymentState, WebhookEvent

class MyProvider(Provider):
    key = "my_gateway"
    name = "My Gateway"
    author = "acme"
    version = "1.0.0"
    description = "Custom in-house payment gateway"
    url = "https://my-gateway.example.com"

    def create_checkout(self, amount, currency, success_url, cancel_url, metadata=None):
        # Call your gateway here; raise UserError on failure
        return CheckoutSession(
            session_id="sess_1",
            redirect_url="https://pay.my-gateway.com/sess_1",
            provider=self.key,
            amount=amount,
            currency=currency,
        )

    def get_payment(self, payment_id):
        return PaymentStatus(payment_id=payment_id, state=PaymentState.PENDING, provider=self.key)

    def parse_webhook(self, payload, headers):
        from merchants.webhooks import parse_event
        return parse_event(payload, provider=self.key)
```

## Provider Metadata

Every provider exposes structured metadata through the `ProviderInfo` Pydantic model.
Downstream applications can inspect the registry, serialise it to JSON, or drive
routing logic without knowing provider implementation details.

### Required fields for new providers

| Field | Type | Description |
|---|---|---|
| `key` | `str` | Short machine-readable identifier (e.g. `"stripe"`) |
| `name` | `str` | Human-readable name (e.g. `"Stripe"`) |
| `author` | `str` | Author/maintainer of the integration |
| `version` | `str` | Version string for this integration |
| `description` | `str` | Short description *(optional, defaults to `""`)* |
| `url` | `str` | Homepage or docs URL *(optional, defaults to `""`)* |

### Inspecting a single provider

```python
from merchants.providers.dummy import DummyProvider
import merchants

provider = DummyProvider()
info = provider.get_info()   # returns a ProviderInfo pydantic model

print(info.key)          # "dummy"
print(info.name)         # "Dummy"
print(info.author)       # "merchants team"
print(info.model_dump()) # {'key': 'dummy', 'name': 'Dummy', ...}
print(info.model_dump_json(indent=2))  # JSON string
```

### Inspecting all registered providers

```python
from merchants import register_provider, describe_providers
from merchants.providers.dummy import DummyProvider
from merchants.providers.stripe import StripeProvider

register_provider(DummyProvider())
register_provider(StripeProvider(api_key="sk_test_…"))

for info in describe_providers():
    print(f"{info.key}: {info.name} v{info.version}")
# dummy: Dummy v1.0.0
# stripe: Stripe v1.0.0

# Serialise the entire registry to JSON
import json
print(json.dumps([i.model_dump() for i in describe_providers()], indent=2))
```

## CLI

Install the CLI extra and use the `merchants` command:

```bash
pip install "merchants[cli]"
merchants --help
```

```
 merchants – framework-agnostic hosted-checkout payment SDK.

╭─ Commands ───────────────────────────────────────────────────────────╮
│ version     Show the merchants package version.                      │
│ providers   List all registered payment providers.                   │
│ info        Show metadata for a registered provider.                 │
│ payments    Create checkout sessions, retrieve payment status, …     │
╰──────────────────────────────────────────────────────────────────────╯
```

**Show the package version:**

```bash
merchants version
# merchants 0.1.0
```

**List registered providers (table or JSON):**

```bash
merchants providers
# Key          Name       Author           Version
# -------------------------------------------------------
# dummy        Dummy      merchants team   1.0.0

merchants providers --output json
# [{"key": "dummy", "name": "Dummy", ...}]
```

**Show metadata for a specific provider:**

```bash
merchants info dummy
# Key         : dummy
# Name        : Dummy
# Author      : merchants team
# Version     : 1.0.0
# Description : Local development provider …
# URL         :

merchants info stripe --output json
# {"key": "stripe", "name": "Stripe", ...}
```

**Create a checkout session:**

```bash
# DummyProvider – no credentials needed, great for testing
merchants payments checkout \
  --provider dummy \
  --amount 19.99 \
  --currency USD \
  --success-url https://example.com/ok \
  --cancel-url https://example.com/cancel
# Session ID  : dummy_sess_abc123
# Redirect URL: https://dummy-pay.example.com/pay/dummy_sess_abc123?...
# Provider    : dummy
# Amount      : 19.99 USD

# With metadata and JSON output
merchants payments checkout \
  --provider dummy \
  --amount 49.99 \
  --currency EUR \
  --success-url https://example.com/ok \
  --cancel-url https://example.com/cancel \
  --metadata '{"order_id": "ORD-42"}' \
  --output json
```

Built-in providers read credentials from environment variables:

| Provider | Environment variable(s) |
|---|---|
| `stripe` | `STRIPE_API_KEY` |
| `paypal` | `PAYPAL_ACCESS_TOKEN` |
| `generic` | `GENERIC_CHECKOUT_URL`, `GENERIC_PAYMENT_URL` |

```bash
STRIPE_API_KEY=sk_test_… merchants payments checkout \
  --provider stripe --amount 9.99 --currency USD \
  --success-url https://example.com/ok \
  --cancel-url https://example.com/cancel
```

**Get payment status:**

```bash
merchants payments get pay_abc123 --provider dummy
# Payment ID  : pay_abc123
# State       : succeeded
# Provider    : dummy
# Final       : yes
# Success     : yes

merchants payments get pay_abc123 --provider dummy --output json
```

**Parse and verify a webhook:**

```bash
# Parse a webhook payload from a file
merchants payments webhook --file payload.json --provider stripe

# Verify HMAC-SHA256 signature before parsing
merchants payments webhook \
  --file payload.json \
  --provider stripe \
  --secret whsec_… \
  --signature "sha256=abc123…"
# Event ID    : evt_…
# Event Type  : payment_intent.succeeded
# Payment ID  : pi_…
# State       : succeeded
# Provider    : stripe
# Verified    : yes

# Or pipe from stdin
cat payload.json | merchants payments webhook --provider stripe
```

## Checkout Creation

```python
try:
    session = client.payments.create_checkout(
        amount="99.00",
        currency="EUR",
        success_url="https://shop.example.com/thank-you",
        cancel_url="https://shop.example.com/cart",
    )
    return redirect(session.redirect_url)
except merchants.UserError as e:
    return f"Payment setup failed: {e}", 400
```

## Payment Status

```python
status = client.payments.get("pi_3LHpu2…")

print(status.state)        # e.g. PaymentState.SUCCEEDED
print(status.is_final)     # True once payment is terminal
print(status.is_success)   # True only when SUCCEEDED
```

## Webhook Verification & Parsing

```python
import merchants

# 1. Verify signature (constant-time HMAC-SHA256)
try:
    merchants.verify_signature(
        payload=request.body,          # raw bytes
        secret="whsec_…",
        signature=request.headers["Stripe-Signature"],
    )
except merchants.WebhookVerificationError:
    return 400  # reject

# 2. Parse and normalise the event
event = merchants.parse_event(request.body, provider="stripe")

print(event.event_type)  # e.g. "payment_intent.succeeded"
print(event.state)       # e.g. PaymentState.SUCCEEDED
print(event.payment_id)  # e.g. "pi_3LHpu2…"
```

## Amount Format Notes

| Helper | Example | Use case |
|---|---|---|
| `to_decimal_string("19.99")` | `"19.99"` | PayPal, most REST APIs |
| `to_minor_units("19.99")` | `1999` | Stripe (cents/pence) |
| `from_minor_units(1999)` | `Decimal("19.99")` | Converting Stripe amounts back |

```python
from merchants import to_decimal_string, to_minor_units, from_minor_units
from decimal import Decimal

to_decimal_string(Decimal("9.5"))   # "9.50"
to_minor_units("19.99")             # 1999
to_minor_units("1000", decimals=0)  # 1000  (JPY, no cents)
from_minor_units(1999)              # Decimal("19.99")
```

## Auth Strategies

```python
from merchants import Client, ApiKeyAuth, TokenAuth
from merchants.providers.generic import GenericProvider

# API key header
client = Client(
    provider=GenericProvider("https://api.example.com/checkout", "https://api.example.com/payments/{payment_id}"),
    auth=ApiKeyAuth("my-key", header="X-API-Key"),
)

# Bearer token
client = Client(
    provider=...,
    auth=TokenAuth("my-token"),   # Authorization: Bearer my-token
)
```

## Custom Transport

```python
from merchants import Client, RequestsTransport

# Inject a pre-configured requests.Session (e.g. with retries)
import requests
from requests.adapters import HTTPAdapter, Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5)
session.mount("https://", HTTPAdapter(max_retries=retry))

client = Client(
    provider="stripe",
    transport=RequestsTransport(session=session),
)
```

## Low-level Escape Hatch

```python
response = client.request("GET", "https://api.stripe.com/v1/balance")
print(response.status_code, response.body)
```

## Examples

The `examples/` directory contains runnable scripts:

| File | Description |
|---|---|
| `01_simple_client.py` | Basic client setup with DummyProvider and Stripe |
| `02_custom_httpx_transport.py` | Custom httpx-backed transport |
| `03_custom_provider.py` | Building your own provider |

## Development

```bash
pip install -e ".[dev]"
pytest
```

The package version is maintained in a single place: `src/merchants/version.py`.
Update `__version__` there and it propagates to the package metadata, `merchants.__version__`,
and the `merchants version` CLI command automatically.

## License

MIT
