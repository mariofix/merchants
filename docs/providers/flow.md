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
| `api_secret` | `str` | required | Flow.cl API secret |
| `sandbox` | `bool` | `False` | Use Flow sandbox environment |

!!! tip "Test in sandbox first"
    Set `sandbox=True` to direct all requests to Flow's sandbox environment. Get sandbox credentials from your [Flow.cl merchant account](https://www.flow.cl).

## State Mapping

| Flow status | `PaymentState` |
|---|---|
| `1` (pending) | `PENDING` |
| `2` (paid) | `SUCCEEDED` |
| `3` (rejected) | `FAILED` |
| `4` (cancelled) | `CANCELLED` |
