# Flow.cl Provider

The `FlowProvider` integrates with [Flow.cl](https://www.flow.cl), a Chilean payment gateway, via the [`pyflowcl`](https://pypi.org/project/pyflowcl/) package.

## Installation

Install merchants with the `flow` extra:

```bash
pip install "merchants[flow]"
```

!!! note "Requires pyflowcl"
    The `flow` extra installs [`pyflowcl`](https://pypi.org/project/pyflowcl/). If `pyflowcl` is not installed, importing `FlowProvider` raises an `ImportError` with installation instructions.

## Usage

```python
from merchants import Client
from merchants.providers.flow import FlowProvider

provider = FlowProvider(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="9990",
    currency="CLP",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
    metadata={"order_id": "ord_456"},
)
print(session.redirect_url)  # redirect the user to Flow here
```

## Payment Status

```python
status = client.payments.get("FLOW_ORDER_NUMBER")

print(status.state)       # e.g. PaymentState.SUCCEEDED
print(status.amount)      # e.g. Decimal("9990")
print(status.currency)    # "CLP"
```

## Webhook Parsing

```python
import merchants

event = merchants.parse_event(payload, provider="flow")
print(event.event_type)   # "payment.notification"
print(event.payment_id)   # Flow order number
print(event.state)        # e.g. PaymentState.SUCCEEDED
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Flow.cl API key |
| `api_secret` | `str` | required | Flow.cl API secret (used for HMAC-SHA256 request signing) |
| `api_url` | `str` | `"https://www.flow.cl/api"` | Override the base API URL |
| `subject` | `str` | `"Order"` | Default payment subject / description |
| `confirmation_url` | `str` | `""` | URL Flow calls after payment is processed |

!!! tip "Test with Flow's sandbox"
    Set `api_url="https://sandbox.flow.cl/api"` to direct requests to the Flow sandbox environment. Get sandbox credentials from your [Flow.cl merchant account](https://www.flow.cl).

!!! warning "Flow webhooks require `confirmation_url`"
    Flow uses `confirmation_url` for server-to-server payment notifications. When the webhook fires, call `client.payments.get(token)` to retrieve the actual payment state, as `parse_webhook` always returns `PaymentState.UNKNOWN`.

## State Mapping

| Flow numeric status | Description | `PaymentState` |
|---|---|---|
| `1` | Paid | `SUCCEEDED` |
| `2` | Rejected | `FAILED` |
| `3` | Pending | `PENDING` |
| `4` | Cancelled | `CANCELLED` |
