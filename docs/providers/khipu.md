# Khipu Provider

The `KhipuProvider` integrates with [Khipu](https://khipu.com), a Chilean bank-transfer payment platform, via the [`khipu-tools`](https://pypi.org/project/khipu-tools/) package.

## Installation

Install merchants with the `khipu` extra:

```bash
pip install "merchants[khipu]"
```

!!! note "Requires khipu-tools"
    The `khipu` extra installs [`khipu-tools`](https://pypi.org/project/khipu-tools/). If it is not installed, importing `KhipuProvider` raises an `ImportError` with installation instructions.

## Usage

```python
from merchants import Client
from merchants.providers.khipu import KhipuProvider

provider = KhipuProvider(
    api_key="YOUR_RECEIVER_API_KEY",
    subject="Order #456",
    notify_url="https://example.com/webhooks/khipu",
)
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="15000",
    currency="CLP",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    metadata={"order_id": "ord_456"},
)
print(session.redirect_url)  # redirect the user to Khipu here
```

## Payment Status

```python
status = client.payments.get("KHIPU_PAYMENT_ID")

print(status.state)       # e.g. PaymentState.SUCCEEDED
print(status.amount)      # e.g. Decimal("15000")
print(status.currency)    # "CLP"
```

## Webhook Parsing

Khipu sends `application/x-www-form-urlencoded` or JSON payloads. Both are handled automatically:

```python
import merchants

event = merchants.parse_event(payload, provider="khipu")
print(event.event_type)   # "payment.notification"
print(event.payment_id)   # Khipu payment ID
print(event.state)        # e.g. PaymentState.SUCCEEDED
```

!!! info "Form-encoded and JSON both supported"
    Khipu may send either a JSON body or a URL-encoded form body depending on the API version. `KhipuProvider.parse_webhook` automatically detects and handles both formats.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Khipu receiver API key |
| `subject` | `str` | `"Order"` | Default payment subject sent to Khipu |
| `notify_url` | `str` | `""` | Webhook URL Khipu will POST when payment is confirmed |

## State Mapping

| Khipu status | `PaymentState` |
|---|---|
| `pending` | `PENDING` |
| `verifying` | `PROCESSING` |
| `done` | `SUCCEEDED` |
| `rejected` | `FAILED` |
| `expired` | `CANCELLED` |
| `reversed` | `REFUNDED` |
