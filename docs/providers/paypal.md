# PayPal Provider

The `PayPalProvider` integrates with the PayPal Orders API. It sends amounts as **decimal strings** (e.g. `"19.99"`) as required by PayPal.

!!! note
    This is a stub that demonstrates the PayPal integration pattern. Replace `base_url` and inject a real transport to connect to the live PayPal API.

## Installation

No extra dependencies required:

```bash
pip install merchants
```

## Usage

```python
from merchants import Client
from merchants.providers.paypal import PayPalProvider

provider = PayPalProvider(access_token="ACCESS_TOKEN")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="49.99",
    currency="USD",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
print(session.redirect_url)  # redirect the user to PayPal here
```

!!! info "Access tokens expire"
    PayPal OAuth access tokens are short-lived. In production, implement a token refresh mechanism and pass a fresh token when creating the provider.

## Amount Handling

PayPal accepts amounts as decimal strings. The provider converts amounts using `to_decimal_string`:

```python
from merchants import to_decimal_string

to_decimal_string("49.9")   # "49.90"
to_decimal_string(49)       # "49.00"
```

## Payment Status

```python
status = client.payments.get("ORDER_ID")

print(status.state)       # e.g. PaymentState.SUCCEEDED
print(status.amount)      # e.g. Decimal("49.99")
print(status.currency)    # e.g. "USD"
```

## Webhook Parsing

```python
import merchants

event = merchants.parse_event(payload, provider="paypal")
print(event.event_type)   # e.g. "PAYMENT.CAPTURE.COMPLETED"
print(event.payment_id)   # e.g. "ORDER_ID"
print(event.state)        # PaymentState.SUCCEEDED
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `access_token` | `str` | required | PayPal OAuth access token |
| `base_url` | `str` | `"https://api-m.paypal.com"` | Override for testing |
| `transport` | `Transport \| None` | `None` | Custom HTTP transport |

!!! tip "Use the sandbox for testing"
    Override `base_url` to `"https://api-m.sandbox.paypal.com"` and use sandbox credentials to test without processing real payments.

## State Mapping

| PayPal status | `PaymentState` |
|---|---|
| `CREATED` | `PENDING` |
| `APPROVED` | `PROCESSING` |
| `COMPLETED` | `SUCCEEDED` |
| `VOIDED` | `CANCELLED` |
| `REFUNDED` | `REFUNDED` |
