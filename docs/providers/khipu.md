# Khipu Provider

The `KhipuProvider` integrates with [Khipu](https://khipu.com), a Chilean bank-transfer payment platform, via the [`khipu-tools`](https://pypi.org/project/khipu-tools/) package.

## Installation

Install merchants with the `khipu` extra:

```bash
pip install "merchants-sdk[khipu]"
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

`KhipuProvider.parse_webhook` handles Khipu v3.0 JSON payloads. When `webhook_secret` is configured, it verifies the `x-khipu-signature` header using HMAC-SHA256 before parsing.

```python
# Use provider's parse_webhook for signature verification
provider = KhipuProvider(
    api_key="YOUR_RECEIVER_API_KEY",
    webhook_secret="YOUR_WEBHOOK_SECRET",
)
client = Client(provider=provider)

# Access the provider directly to use parse_webhook
event = client._provider.parse_webhook(request.body, dict(request.headers))
print(event.event_type)   # "payment.conciliated" or "payment.notification"
print(event.payment_id)   # Khipu payment ID
print(event.state)        # e.g. PaymentState.SUCCEEDED
```

!!! info "JSON and form-encoded both supported"
    `KhipuProvider.parse_webhook` automatically detects and handles both JSON and URL-encoded form bodies. The v3.0 API sends JSON.

!!! note "State detection from `conciliation_date`"
    In v3.0, the payment state is determined by the presence of `conciliation_date` in the payload. If present, the state is `SUCCEEDED` and the event type is `"payment.conciliated"`. Otherwise `payment_status` is used with the standard state map.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Khipu receiver API key |
| `subject` | `str` | `"Order"` | Default payment subject sent to Khipu |
| `notify_url` | `str` | `""` | Webhook URL Khipu will POST when payment is confirmed |
| `webhook_secret` | `str` | `""` | Webhook signing secret for HMAC-SHA256 signature verification |

## State Mapping

| Khipu status | `PaymentState` |
|---|---|
| `pending` | `PENDING` |
| `verifying` | `PROCESSING` |
| `done` | `SUCCEEDED` |
| `rejected` | `FAILED` |
| `expired` | `CANCELLED` |
| `reversed` | `REFUNDED` |
