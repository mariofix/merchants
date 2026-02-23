# Stripe Provider

The `StripeProvider` integrates with Stripe's Checkout Sessions API. It converts amounts to **minor units** (cents) as required by Stripe.

!!! note
    This is a stub that demonstrates the Stripe integration pattern. Replace `base_url` and inject a real transport to connect to the live Stripe API.

## Installation

No extra dependencies required:

```bash
pip install merchants
```

## Usage

```python
from merchants import Client
from merchants.providers.stripe import StripeProvider

provider = StripeProvider(api_key="sk_test_…")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="19.99",
    currency="USD",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    metadata={"order_id": "ord_123"},
)
print(session.redirect_url)  # redirect the user here
```

!!! warning "Use test keys during development"
    Always use `sk_test_…` keys during development. Never commit live keys (`sk_live_…`) to source control — load them from environment variables instead.

## Amount Handling

Stripe requires amounts in the **smallest currency unit** (e.g. cents for USD, pence for GBP). The provider automatically converts decimal amounts using `to_minor_units`:

```python
from merchants import to_minor_units

to_minor_units("19.99")          # 1999 (USD cents)
to_minor_units("1000", decimals=0)  # 1000 (JPY — no subdivision)
```

Zero-decimal currencies (e.g. JPY, BIF, CLP) are handled automatically.

!!! tip "Amount format is handled for you"
    Pass amounts as strings or `Decimal` in standard decimal notation (e.g. `"19.99"`). The provider converts to the correct minor-unit integer automatically.

## Payment Status

After the user completes checkout, retrieve the payment status by `payment_id`:

```python
status = client.payments.get("pi_3LHpu2…")

print(status.state)       # PaymentState.SUCCEEDED
print(status.is_final)    # True
print(status.is_success)  # True
```

## Webhook Parsing

```python
import merchants

event = merchants.parse_event(payload, provider="stripe")
print(event.event_type)   # e.g. "payment_intent.succeeded"
print(event.payment_id)   # e.g. "pi_3LHpu2…"
print(event.state)        # PaymentState.SUCCEEDED
```

!!! tip "Verify before parsing"
    Always call `merchants.verify_signature(...)` before `parse_event`. See the [Webhooks](../webhooks.md) guide for a complete handler example.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Stripe secret key (`sk_test_…` or `sk_live_…`) |
| `base_url` | `str` | `"https://api.stripe.com"` | Override for testing |
| `transport` | `Transport \| None` | `None` | Custom HTTP transport |

## State Mapping

| Stripe status | `PaymentState` |
|---|---|
| `requires_payment_method` | `PENDING` |
| `requires_confirmation` | `PENDING` |
| `requires_action` | `PENDING` |
| `processing` | `PROCESSING` |
| `succeeded` | `SUCCEEDED` |
| `canceled` | `CANCELLED` |
| `failed` | `FAILED` |
